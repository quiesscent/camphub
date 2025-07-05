import hashlib
import os
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


def generate_md5_filename(file_content, original_filename):
    """
    Generate MD5 hash filename while preserving file extension
    """
    file_extension = os.path.splitext(original_filename)[1].lower()
    md5_hash = hashlib.md5(file_content).hexdigest()
    return f"{md5_hash}{file_extension}"


def optimize_image(image_file, max_width=800, max_height=800, quality=85, format_type='JPEG'):
    """
    Optimize image by resizing and compressing while maintaining quality
    """
    try:
        with Image.open(image_file) as img:
            # Convert RGBA to RGB for JPEG format
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Auto-orient image based on EXIF data
            img = ImageOps.exif_transpose(img)
            
            # Calculate new dimensions maintaining aspect ratio
            width, height = img.size
            
            if width > max_width or height > max_height:
                # Calculate resize ratio
                width_ratio = max_width / width
                height_ratio = max_height / height
                resize_ratio = min(width_ratio, height_ratio)
                
                new_width = int(width * resize_ratio)
                new_height = int(height * resize_ratio)
                
                # Use LANCZOS for high quality resizing
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save optimized image to bytes
            output = BytesIO()
            img.save(output, format=format_type, quality=quality, optimize=True)
            output.seek(0)
            
            return output.getvalue()
            
    except Exception as e:
        # If optimization fails, return original file content
        image_file.seek(0)
        return image_file.read()


def process_profile_picture(image_file):
    """
    Process profile picture: optimize and generate MD5 filename
    """
    # Read file content
    image_file.seek(0)
    original_content = image_file.read()
    
    # Optimize image (square format for profile pictures)
    optimized_content = optimize_image(
        BytesIO(original_content),
        max_width=400,
        max_height=400,
        quality=90
    )
    
    # Generate MD5 filename
    filename = generate_md5_filename(optimized_content, image_file.name)
    
    return ContentFile(optimized_content, name=filename)


def process_institution_logo(image_file):
    """
    Process institution logo: optimize and generate MD5 filename
    """
    # Read file content
    image_file.seek(0)
    original_content = image_file.read()
    
    # Optimize image (preserve aspect ratio for logos)
    optimized_content = optimize_image(
        BytesIO(original_content),
        max_width=300,
        max_height=200,
        quality=95
    )
    
    # Generate MD5 filename
    filename = generate_md5_filename(optimized_content, image_file.name)
    
    return ContentFile(optimized_content, name=filename)


def delete_old_image(field_instance):
    """
    Delete old image file when updating
    """
    if field_instance and hasattr(field_instance, 'path'):
        try:
            if default_storage.exists(field_instance.path):
                default_storage.delete(field_instance.path)
        except (ValueError, FileNotFoundError):
            pass


class OptimizedImageField:
    """
    Mixin class for handling optimized image uploads
    """
    @staticmethod
    def save_profile_picture(instance, filename):
        """
        Custom upload path for profile pictures
        """
        return f'profile_pictures/{filename}'
    
    @staticmethod
    def save_institution_logo(instance, filename):
        """
        Custom upload path for institution logos
        """
        return f'institution_logos/{filename}'
