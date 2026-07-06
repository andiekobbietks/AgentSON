"""
PII Redactor for AgentSON files using OpenAI Privacy Filter.
Automatically detects and redacts PII from .agentson files before exporting or sharing.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional


class PIIRedactor:
    """Redact PII from .agentson files using OpenAI Privacy Filter."""
    
    # PII categories from Privacy Filter
    PII_CATEGORIES = [
        "private_person",
        "private_address", 
        "private_email",
        "private_phone",
        "private_url",
        "private_date",
        "account_number",
        "secret"
    ]
    
    def __init__(self, use_model: bool = False):
        """
        Initialize PII Redactor.
        
        Args:
            use_model: If True, use Privacy Filter model (requires GPU)
                       If False, use regex-based detection (faster, less accurate)
        """
        self.use_model = use_model
        self.model = None
        self.tokenizer = None
        
        if use_model:
            self._load_model()
    
    def _load_model(self):
        """Load Privacy Filter model."""
        try:
            from transformers import AutoTokenizer, AutoModelForTokenClassification
            import torch
            
            model_name = "openai/privacy-filter"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.model.eval()
            print(f"Loaded Privacy Filter model: {model_name}")
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Falling back to regex-based detection")
            self.use_model = False
    
    def redact_text(self, text: str) -> tuple[str, List[Dict]]:
        """
        Redact PII from text.
        
        Returns:
            Tuple of (redacted_text, list_of_redactions)
        """
        if not text:
            return text, []
        
        redactions = []
        redacted = text
        
        if self.use_model:
            redacted, redactions = self._redact_with_model(text)
        else:
            redacted, redactions = self._redact_with_regex(text)
        
        return redacted, redactions
    
    def _redact_with_regex(self, text: str) -> tuple[str, List[Dict]]:
        """Regex-based PII detection (fallback)."""
        redactions = []
        redacted = text
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            redactions.append({
                "type": "private_email",
                "text": match.group(),
                "start": match.start(),
                "end": match.end()
            })
            redacted = redacted.replace(match.group(), "[PRIVATE_EMAIL]")
        
        # Phone numbers (strict patterns only)
        phone_patterns = [
            r'\+\d{1,3}[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}',  # +1 (555) 123-4567
            r'\(\d{3}\)\s*\d{3}[\s\-]\d{4}',  # (555) 123-4567
            r'\d{3}[\s\-]\d{3}[\s\-]\d{4}',  # 555-123-4567
            r'\+\d{10,}',  # +1234567890
        ]
        for pattern in phone_patterns:
            for match in re.finditer(pattern, text):
                # Additional validation: must have letters around it (not just numbers)
                start = max(0, match.start() - 5)
                end = min(len(text), match.end() + 5)
                context = text[start:end]
                # Skip if context is mostly numbers/symbols (table data)
                if re.search(r'[A-Za-z]{3,}', context):
                    redactions.append({
                        "type": "private_phone",
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end()
                    })
                    redacted = redacted.replace(match.group(), "[PRIVATE_PHONE]")
        
        # Known secret prefixes (real API keys)
        secret_prefixes = [
            r'ghp_[A-Za-z0-9]{36}',  # GitHub PAT
            r'gho_[A-Za-z0-9]{36}',  # GitHub OAuth
            r'github_pat_[A-Za-z0-9]{82}',  # GitHub fine-grained PAT
            r'sk-[A-Za-z0-9]{48}',  # OpenAI API key
            r'sk_live_[A-Za-z0-9]{32,}',  # Stripe live key
            r'sk_test_[A-Za-z0-9]{32,}',  # Stripe test key
            r'AKIA[A-Z0-9]{16}',  # AWS Access Key
            r'xox[bpas]-[A-Za-z0-9\-]+',  # Slack token
            r'Bearer [A-Za-z0-9\-._~+/]+=*',  # Bearer token
            r'eyJ[A-Za-z0-9\-._]+\.eyJ[A-Za-z0-9\-._]+\.[A-Za-z0-9\-._]+',  # JWT
        ]
        for pattern in secret_prefixes:
            for match in re.finditer(pattern, text):
                redactions.append({
                    "type": "secret",
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
                redacted = redacted.replace(match.group(), "[SECRET]")
        
        # Dates (specific formats)
        date_patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',
            r'\b\d{2}/\d{2}/\d{4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        ]
        for pattern in date_patterns:
            for match in re.finditer(pattern, text):
                redactions.append({
                    "type": "private_date",
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
                redacted = redacted.replace(match.group(), "[PRIVATE_DATE]")
        
        return redacted, redactions
    
    def _redact_with_model(self, text: str) -> tuple[str, List[Dict]]:
        """Use Privacy Filter model for PII detection."""
        import torch
        
        redactions = []
        
        # Tokenize
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128000)
        
        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=-1)
        
        # Decode predictions to spans
        tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        pred_labels = predictions[0].tolist()
        
        # Convert token predictions to spans
        current_span = None
        current_text = ""
        
        for i, (token, pred) in enumerate(zip(tokens, pred_labels)):
            label = self.model.config.id2label.get(pred, "O")
            
            if label.startswith("B-"):
                # Start of new span
                if current_span:
                    redactions.append({
                        "type": current_span,
                        "text": current_text,
                        "start": 0,  # Would need to track positions
                        "end": 0
                    })
                current_span = label[2:]
                current_text = token.replace("##", "")
            elif label.startswith("I-") and current_span:
                # Continuation of span
                current_text += token.replace("##", "")
            elif label.startswith("E-"):
                # End of span
                current_text += token.replace("##", "")
                redactions.append({
                    "type": current_span,
                    "text": current_text,
                    "start": 0,
                    "end": 0
                })
                current_span = None
                current_text = ""
            elif label == "O":
                # Outside any span
                if current_span:
                    redactions.append({
                        "type": current_span,
                        "text": current_text,
                        "start": 0,
                        "end": 0
                    })
                    current_span = None
                    current_text = ""
        
        # Apply redactions
        redacted = text
        for redaction in sorted(redactions, key=lambda x: x["start"], reverse=True):
            placeholder = f"[{redaction['type'].upper()}]"
            redacted = redacted.replace(redaction["text"], placeholder)
        
        return redacted, redactions
    
    def redact_agentson(self, data: Dict) -> tuple[Dict, List[Dict]]:
        """
        Redact PII from an .agentson dictionary.
        
        Returns:
            Tuple of (redacted_data, list_of_all_redactions)
        """
        all_redactions = []
        redacted_data = json.loads(json.dumps(data))  # Deep copy
        
        # Process all entries
        for entry in redacted_data.get("entries", []):
            # Redact text fields
            for field in ["text", "code", "output", "query"]:
                if field in entry and entry[field]:
                    redacted_text, redactions = self.redact_text(str(entry[field]))
                    if redactions:
                        entry[field] = redacted_text
                        all_redactions.extend(redactions)
            
            # Redact args if present
            if "args" in entry and isinstance(entry["args"], dict):
                for key, value in entry["args"].items():
                    if isinstance(value, str):
                        redacted_value, redactions = self.redact_text(value)
                        if redactions:
                            entry["args"][key] = redacted_value
                            all_redactions.extend(redactions)
        
        return redacted_data, all_redactions
    
    def redact_file(self, input_path: str, output_path: str = None) -> Dict:
        """
        Redact PII from an .agentson file.
        
        Args:
            input_path: Path to input .agentson file
            output_path: Path to output .agentson file (if None, overwrites input)
        
        Returns:
            Dictionary with redaction statistics
        """
        # Load file
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Redact
        redacted_data, redactions = self.redact_agentson(data)
        
        # Save
        if output_path is None:
            output_path = input_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(redacted_data, f, indent=2, ensure_ascii=False)
        
        # Return statistics
        stats = {
            "input_file": input_path,
            "output_file": output_path,
            "total_redactions": len(redactions),
            "by_type": {}
        }
        
        for redaction in redactions:
            redaction_type = redaction["type"]
            stats["by_type"][redaction_type] = stats["by_type"].get(redaction_type, 0) + 1
        
        return stats


def redact_all(input_dir: str = "examples", output_dir: str = "examples_redacted"):
    """Redact PII from all .agentson files in a directory."""
    
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    redactor = PIIRedactor(use_model=False)
    
    agentson_files = list(input_path.glob("*.agentson"))
    
    if not agentson_files:
        print(f"No .agentson files found in {input_dir}")
        return
    
    print(f"Found {len(agentson_files)} .agentson files")
    
    total_redactions = 0
    
    for agentson_file in agentson_files:
        try:
            output_file = output_path / agentson_file.name
            stats = redactor.redact_file(str(agentson_file), str(output_file))
            total_redactions += stats["total_redactions"]
            
            if stats["total_redactions"] > 0:
                print(f"Redacted: {agentson_file.name} ({stats['total_redactions']} redactions)")
                for pii_type, count in stats["by_type"].items():
                    print(f"  - {pii_type}: {count}")
        except Exception as e:
            print(f"Error processing {agentson_file.name}: {e}")
    
    print(f"\nTotal redactions: {total_redactions}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Redact PII from AgentSON files")
    parser.add_argument("input", help="Input .agentson file or directory")
    parser.add_argument("--output", help="Output .agentson file or directory")
    parser.add_argument("--all", action="store_true", help="Process all .agentson files in directory")
    parser.add_argument("--model", action="store_true", help="Use Privacy Filter model (requires GPU)")
    args = parser.parse_args()
    
    if args.all:
        redact_all(args.input, args.output or "examples_redacted")
    else:
        redactor = PIIRedactor(use_model=args.model)
        output = args.output or args.input
        stats = redactor.redact_file(args.input, output)
        
        print(f"Redacted: {stats['input_file']} -> {stats['output_file']}")
        print(f"Total redactions: {stats['total_redactions']}")
        for pii_type, count in stats["by_type"].items():
            print(f"  - {pii_type}: {count}")
