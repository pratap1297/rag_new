#!/usr/bin/env python3
"""
Embedding Migration Utility
Helps migrate FAISS index when changing embedding models with different dimensions
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from storage.faiss_store import FAISSStore
from core.embedding_manager import EmbeddingManager
from core.config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EmbeddingMigrator:
    """Utility class for migrating embeddings between different models"""
    
    def __init__(self, config_path: str = "rag_system/.env"):
        self.config = ConfigManager(config_path)
        self.faiss_store = None
        self.embedding_manager = None
        
    def initialize_stores(self, index_path: str = "data/vectors/index.faiss"):
        """Initialize FAISS store and embedding manager"""
        try:
            # Get current embedding configuration
            embedding_provider = self.config.get("RAG_EMBEDDING_PROVIDER", "azure")
            embedding_model = self.config.get("RAG_EMBEDDING_MODEL", "Cohere-embed-v3-english")
            
            # Initialize embedding manager to get current dimension
            self.embedding_manager = EmbeddingManager()
            current_dimension = self.embedding_manager.get_embedding_dimension()
            
            # Initialize FAISS store
            self.faiss_store = FAISSStore(index_path=index_path, dimension=current_dimension)
            
            logging.info(f"Initialized stores with dimension {current_dimension}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize stores: {e}")
            return False
    
    def check_migration_needed(self, new_model: str) -> dict:
        """Check if migration is needed for new embedding model"""
        if not self.faiss_store or not self.embedding_manager:
            logging.error("Stores not initialized")
            return {}
        
        # Get new model dimension
        try:
            # Temporarily change config to test new model
            original_model = self.config.get("RAG_EMBEDDING_MODEL")
            self.config.set("RAG_EMBEDDING_MODEL", new_model)
            
            new_embedding_manager = EmbeddingManager()
            new_dimension = new_embedding_manager.get_embedding_dimension()
            
            # Restore original config
            self.config.set("RAG_EMBEDDING_MODEL", original_model)
            
            # Check compatibility
            compatibility = self.faiss_store.check_dimension_compatibility(new_dimension)
            compatibility['new_model'] = new_model
            compatibility['new_dimension'] = new_dimension
            
            return compatibility
            
        except Exception as e:
            logging.error(f"Failed to check migration: {e}")
            return {}
    
    def migrate_with_rebuild(self, new_model: str, index_path: str = "data/vectors/index.faiss") -> bool:
        """Migrate by force rebuilding (loses all vectors)"""
        if not self.faiss_store:
            logging.error("FAISS store not initialized")
            return False
        
        try:
            # Get new model dimension
            original_model = self.config.get("RAG_EMBEDDING_MODEL")
            self.config.set("RAG_EMBEDDING_MODEL", new_model)
            
            new_embedding_manager = EmbeddingManager()
            new_dimension = new_embedding_manager.get_embedding_dimension()
            
            # Restore original config
            self.config.set("RAG_EMBEDDING_MODEL", original_model)
            
            logging.info(f"Migrating to {new_model} with dimension {new_dimension}")
            
            # Force rebuild
            success = self.faiss_store.force_rebuild_for_new_dimension(new_dimension)
            
            if success:
                # Update config
                self.config.set("RAG_EMBEDDING_MODEL", new_model)
                self.config.save()
                logging.info(f"Successfully migrated to {new_model}")
                return True
            else:
                logging.error("Failed to rebuild index")
                return False
                
        except Exception as e:
            logging.error(f"Migration failed: {e}")
            return False
    
    def migrate_with_reembedding(self, new_model: str, original_texts: List[str]) -> bool:
        """Migrate by re-embedding original texts"""
        if not self.faiss_store:
            logging.error("FAISS store not initialized")
            return False
        
        if not original_texts:
            logging.error("No original texts provided")
            return False
        
        try:
            # Get new model dimension and embedder
            original_model = self.config.get("RAG_EMBEDDING_MODEL")
            self.config.set("RAG_EMBEDDING_MODEL", new_model)
            
            new_embedding_manager = EmbeddingManager()
            new_dimension = new_embedding_manager.get_embedding_dimension()
            
            # Restore original config
            self.config.set("RAG_EMBEDDING_MODEL", original_model)
            
            logging.info(f"Migrating to {new_model} with dimension {new_dimension}")
            
            # Migrate using re-embedding
            success = self.faiss_store.migrate_to_new_dimension(
                new_dimension=new_dimension,
                new_embedder=new_embedding_manager,
                original_texts=original_texts
            )
            
            if success:
                # Update config
                self.config.set("RAG_EMBEDDING_MODEL", new_model)
                self.config.save()
                logging.info(f"Successfully migrated to {new_model}")
                return True
            else:
                logging.error("Failed to migrate with re-embedding")
                return False
                
        except Exception as e:
            logging.error(f"Migration failed: {e}")
            return False
    
    def extract_original_texts(self) -> List[str]:
        """Extract original texts from current FAISS index metadata"""
        if not self.faiss_store:
            logging.error("FAISS store not initialized")
            return []
        
        try:
            all_metadata = self.faiss_store.get_all_metadata()
            texts = []
            
            for vector_id, metadata in all_metadata.items():
                if metadata and not metadata.get('deleted', False):
                    text = metadata.get('text', metadata.get('content', ''))
                    if text:
                        texts.append(text)
            
            logging.info(f"Extracted {len(texts)} original texts from index")
            return texts
            
        except Exception as e:
            logging.error(f"Failed to extract original texts: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description="Migrate embeddings between different models")
    parser.add_argument("--new-model", required=True, help="New embedding model name")
    parser.add_argument("--index-path", default="data/vectors/index.faiss", help="Path to FAISS index")
    parser.add_argument("--config-path", default="rag_system/.env", help="Path to config file")
    parser.add_argument("--strategy", choices=["check", "rebuild", "reembed"], default="check",
                       help="Migration strategy")
    parser.add_argument("--texts-file", help="File containing original texts (for reembed strategy)")
    parser.add_argument("--force", action="store_true", help="Force migration without confirmation")
    
    args = parser.parse_args()
    
    # Initialize migrator
    migrator = EmbeddingMigrator(args.config_path)
    
    if not migrator.initialize_stores(args.index_path):
        sys.exit(1)
    
    # Check migration compatibility
    compatibility = migrator.check_migration_needed(args.new_model)
    
    if not compatibility:
        logging.error("Failed to check compatibility")
        sys.exit(1)
    
    print(f"\nMigration Analysis:")
    print(f"  Current model: {migrator.config.get('RAG_EMBEDDING_MODEL')}")
    print(f"  New model: {args.new_model}")
    print(f"  Current dimension: {compatibility['current_dimension']}")
    print(f"  New dimension: {compatibility['new_dimension']}")
    print(f"  Vector count: {compatibility['vector_count']}")
    print(f"  Migration required: {compatibility['migration_required']}")
    
    if not compatibility['migration_required']:
        print("\nNo migration needed - dimensions are compatible!")
        return
    
    if args.strategy == "check":
        print("\nMigration options:")
        for option in compatibility['migration_options']:
            print(f"  - {option['type']}: {option['description']}")
        return
    
    # Confirm migration
    if not args.force:
        response = input(f"\nAre you sure you want to migrate to {args.new_model}? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled")
            return
    
    # Perform migration
    success = False
    
    if args.strategy == "rebuild":
        print(f"\nMigrating with rebuild strategy (will lose all vectors)...")
        success = migrator.migrate_with_rebuild(args.new_model, args.index_path)
        
    elif args.strategy == "reembed":
        print(f"\nMigrating with re-embedding strategy...")
        
        if args.texts_file and os.path.exists(args.texts_file):
            # Load texts from file
            with open(args.texts_file, 'r', encoding='utf-8') as f:
                original_texts = [line.strip() for line in f if line.strip()]
        else:
            # Extract texts from current index
            print("Extracting original texts from current index...")
            original_texts = migrator.extract_original_texts()
        
        if original_texts:
            success = migrator.migrate_with_reembedding(args.new_model, original_texts)
        else:
            logging.error("No original texts available for re-embedding")
            success = False
    
    if success:
        print(f"\n✅ Successfully migrated to {args.new_model}")
    else:
        print(f"\n❌ Failed to migrate to {args.new_model}")
        sys.exit(1)

if __name__ == "__main__":
    main() 