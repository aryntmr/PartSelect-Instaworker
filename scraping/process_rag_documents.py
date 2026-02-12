"""
Processing script to clean up RAG documents by removing unnecessary fields
and extracting topic information from blogs.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any


def extract_topic_from_url(topic_source: str) -> str:
    """
    Extract topic from topic_source URL.
    Example: https://www.partselect.com/blog/topics/repair -> repair
    """
    if not topic_source:
        return ""
    
    # Get the last segment of the URL path
    path_segments = topic_source.rstrip('/').split('/')
    if path_segments:
        return path_segments[-1]
    return ""


def process_parts_json(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process parts JSON files by removing unnecessary fields.
    
    Removes: part_id, difficulty, repair_time, has_video, video_urls, video_count, scraped_at
    """
    fields_to_remove = [
        'part_id', 'difficulty', 'repair_time', 
        'has_video', 'video_urls', 'video_count', 'scraped_at'
    ]
    
    processed_data = []
    for item in data:
        processed_item = {k: v for k, v in item.items() if k not in fields_to_remove}
        processed_data.append(processed_item)
    
    return processed_data


def process_blogs_json(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process blogs JSON files by removing unnecessary fields and adding topic.
    
    Removes: published_date, reading_time, categories, featured_image, images, 
             image_count, related_parts, related_parts_count, video_urls, 
             video_count, scraped_at
    Adds: topic (extracted from topic_source)
    """
    fields_to_remove = [
        'published_date', 'reading_time', 'categories', 
        'featured_image', 'images', 'image_count',
        'related_parts', 'related_parts_count', 
        'video_urls', 'video_count', 'scraped_at'
    ]
    
    processed_data = []
    for item in data:
        # Remove unnecessary fields
        processed_item = {k: v for k, v in item.items() if k not in fields_to_remove}
        
        # Extract and add topic from topic_source
        if 'topic_source' in item:
            processed_item['topic'] = extract_topic_from_url(item['topic_source'])
        
        processed_data.append(processed_item)
    
    return processed_data


def process_file(input_path: Path, output_path: Path, file_type: str) -> None:
    """
    Process a single JSON file.
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file
        file_type: 'parts' or 'blogs'
    """
    print(f"Processing {input_path.name}...")
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process data based on type
    if file_type == 'parts':
        processed_data = process_parts_json(data)
    elif file_type == 'blogs':
        processed_data = process_blogs_json(data)
    else:
        raise ValueError(f"Unknown file type: {file_type}")
    
    # Write output file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Processed {len(data)} items")
    print(f"  ✓ Saved to {output_path}")


def main():
    """Main processing function."""
    # Define paths
    script_dir = Path(__file__).parent
    rag_docs_dir = script_dir / 'data' / 'rag_documents'
    processed_dir = script_dir / 'data' / 'processed'
    
    # Create processed directory if it doesn't exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("RAG Documents Processing Script")
    print("=" * 60)
    print()
    
    # Define files to process
    files_to_process = [
        ('dishwasher_parts.json', 'parts'),
        ('refrigerator_parts.json', 'parts'),
        ('dishwasher_blogs.json', 'blogs'),
        ('refrigerator_blogs.json', 'blogs'),
    ]
    
    # Process each file
    for filename, file_type in files_to_process:
        input_path = rag_docs_dir / filename
        output_path = processed_dir / filename
        
        if input_path.exists():
            try:
                process_file(input_path, output_path, file_type)
                print()
            except Exception as e:
                print(f"  ✗ Error processing {filename}: {e}")
                print()
        else:
            print(f"  ⚠ File not found: {filename}")
            print()
    
    print("=" * 60)
    print("Processing complete!")
    print(f"Processed files saved to: {processed_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
