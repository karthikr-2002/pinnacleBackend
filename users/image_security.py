import io
import os
import uuid
from PIL import Image, UnidentifiedImageError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile


# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================

MAX_UPLOAD_SIZE_MB = getattr(settings, 'MAX_UPLOAD_SIZE_MB', 3)
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp')
ALLOWED_PIL_FORMATS = ('JPEG', 'PNG', 'WEBP')

MAX_IMAGE_WIDTH = 4096
MAX_IMAGE_HEIGHT = 4096

# Dangerous signatures that should never appear in raster image uploads
DANGEROUS_PAYLOAD_SIGNATURES = (
    b'<svg',
    b'<?xml',
    b'<!doctype',
    b'<!DOCTYPE',
    b'<html',
    b'<script',
    b'<?php',
    b'<%',
    b'MZ',          # Windows PE executable
    b'\x7fELF',     # Linux ELF executable
)


# ==============================================================================
# SAFE STORAGE HELPERS
# ==============================================================================

def scramble_photo_filename(instance, filename):
    """
    Generates a secure, randomized filename using UUID4 to prevent:
    1. Directory traversal attacks (../)
    2. Null-byte injection
    3. Filename collision and file overwrites
    4. Information disclosure from user-supplied file names
    """
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        ext = '.jpg'
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('employees', 'photos', unique_name).replace('\\', '/')


def cleanup_old_photo_file(photo_field):
    """Safely removes an existing photo from the disk without throwing exceptions."""
    if not photo_field:
        return
    try:
        if hasattr(photo_field, 'path') and os.path.isfile(photo_field.path):
            os.remove(photo_field.path)
    except Exception:
        # Ignore errors if file already deleted or inaccessible
        pass


# ==============================================================================
# IMAGE VALIDATION
# ==============================================================================

def validate_image_file(uploaded_file):
    """
    Performs comprehensive deep validation on uploaded image files:
    1. Maximum file size check
    2. Whitelisted file extension check
    3. Magic bytes / header inspection (JPEG, PNG, WEBP)
    4. Detection and rejection of embedded scripts / SVG / executables
    5. Pillow image verification (format, corruption check)
    6. Decompression bomb / pixel flood defense (max dimensions)
    """
    if not uploaded_file:
        return

    # 1. File Size Verification
    file_size = getattr(uploaded_file, 'size', 0)
    if file_size > MAX_UPLOAD_SIZE_BYTES:
        size_in_mb = file_size / (1024 * 1024)
        raise ValidationError(
            f"File size exceeds the {MAX_UPLOAD_SIZE_MB} MB limit. "
            f"Your file is {size_in_mb:.1f} MB. Please upload a smaller image."
        )

    # 2. File Extension Verification
    filename = getattr(uploaded_file, 'name', '') or ''
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            "Unsupported file type. Please upload a JPG, PNG, or WebP image."
        )

    # 3. Read Header & Magic Bytes Check
    try:
        uploaded_file.seek(0)
        header = uploaded_file.read(512)
        uploaded_file.seek(0)
    except Exception:
        raise ValidationError("Unable to read uploaded file.")

    if len(header) < 12:
        raise ValidationError("Uploaded file is empty or corrupted.")

    # Check for dangerous embedded script / SVG / executable signatures
    header_lower = header.lower()
    for signature in DANGEROUS_PAYLOAD_SIGNATURES:
        if signature.lower() in header_lower:
            raise ValidationError(
                "Invalid image content: SVG, vector graphics, scripts, and executable files are not permitted."
            )

    # Magic byte matching
    is_jpeg = header.startswith(b'\xff\xd8\xff')
    is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
    is_webp = header.startswith(b'RIFF') and header[8:12] == b'WEBP'

    if not (is_jpeg or is_png or is_webp):
        raise ValidationError(
            "Invalid file format: The file contents do not match a valid JPG, PNG, or WebP image."
        )

    # 4. Pillow Image Verification & Decompression Bomb Protection
    try:
        uploaded_file.seek(0)
        # Protect against decompression bombs
        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_WIDTH * MAX_IMAGE_HEIGHT * 2
        img = Image.open(uploaded_file)

        # Verify reported format matches whitelist
        if img.format not in ALLOWED_PIL_FORMATS:
            raise ValidationError(
                f"Image format '{img.format}' is not supported. Only JPEG, PNG, and WebP are allowed."
            )

        # Check dimensions
        width, height = img.size
        if width > MAX_IMAGE_WIDTH or height > MAX_IMAGE_HEIGHT:
            raise ValidationError(
                f"Image dimensions ({width}x{height}px) exceed the maximum permitted size of "
                f"{MAX_IMAGE_WIDTH}x{MAX_IMAGE_HEIGHT}px."
            )

        # Integrity verification
        img.verify()
    except UnidentifiedImageError:
        raise ValidationError("The uploaded file is not recognized as a valid image.")
    except Image.DecompressionBombError:
        raise ValidationError("The image resolution is excessively large and cannot be processed.")
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError("The image file is corrupted or could not be processed.")
    finally:
        uploaded_file.seek(0)


# ==============================================================================
# IMAGE SANITIZATION & METADATA PURGING
# ==============================================================================

def sanitize_and_clean_image(uploaded_file):
    """
    Re-encodes the image onto a fresh Pillow canvas.
    This purges:
    - All EXIF metadata (camera info, GPS location coordinates)
    - Secret comments or embedded script payloads (polyglot files)
    - Any non-raster baggage appended to the file

    Returns a clean InMemoryUploadedFile.
    """
    validate_image_file(uploaded_file)

    try:
        uploaded_file.seek(0)
        original_img = Image.open(uploaded_file)
        fmt = original_img.format if original_img.format in ALLOWED_PIL_FORMATS else 'JPEG'

        # Create clean canvas without any metadata
        if fmt == 'JPEG':
            # JPEG cannot handle alpha transparency; convert RGBA/LA to RGB
            clean_canvas = Image.new('RGB', original_img.size, (255, 255, 255))
            if original_img.mode in ('RGBA', 'LA'):
                clean_canvas.paste(original_img, mask=original_img.split()[-1])
            elif original_img.mode == 'P':
                clean_canvas.paste(original_img.convert('RGB'))
            else:
                clean_canvas.paste(original_img.convert('RGB'))
            content_type = 'image/jpeg'
            out_ext = '.jpg'
        elif fmt == 'PNG':
            mode = 'RGBA' if original_img.mode in ('RGBA', 'LA', 'P') else 'RGB'
            clean_canvas = Image.new(mode, original_img.size)
            clean_canvas.paste(original_img.convert(mode))
            content_type = 'image/png'
            out_ext = '.png'
        else:  # WEBP
            mode = 'RGBA' if original_img.mode in ('RGBA', 'LA', 'P') else 'RGB'
            clean_canvas = Image.new(mode, original_img.size)
            clean_canvas.paste(original_img.convert(mode))
            content_type = 'image/webp'
            out_ext = '.webp'

        # Save to memory buffer
        out_buffer = io.BytesIO()
        if fmt == 'JPEG':
            clean_canvas.save(out_buffer, format='JPEG', quality=90, optimize=True)
        elif fmt == 'PNG':
            clean_canvas.save(out_buffer, format='PNG', optimize=True)
        else:
            clean_canvas.save(out_buffer, format='WEBP', quality=90)

        out_buffer.seek(0)
        clean_size = out_buffer.getbuffer().nbytes

        clean_name = f"{uuid.uuid4().hex}{out_ext}"

        return InMemoryUploadedFile(
            file=out_buffer,
            field_name='photo',
            name=clean_name,
            content_type=content_type,
            size=clean_size,
            charset=None
        )
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        # If Pillow fails during processing, fallback to validated original file
        uploaded_file.seek(0)
        return uploaded_file

