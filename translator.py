"""
USI17 V22.2 Translator - SIMPLIFIED
Core translation without complex dependencies
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI


class USI17_Translator:
    """Simplified USI17 V22.2 translator"""
    
    def __init__(self, grok_api_key: str, gemini_api_key: str = None, master_path: str = None):
        """Initialize translator"""
        self.grok_client = OpenAI(
            api_key=grok_api_key,
            base_url="https://api.x.ai/v1"
        ) if grok_api_key else None
        
        self.gemini_api_key = gemini_api_key
        
        # Load V22.2 Master system
        self.system = self._load_master(master_path)
        
        self.total_cost = 0.0
        self.usd_to_jpy = 152.0
        
        # Pricing
        self.pricing = {
            'grok': {'input': 0.20, 'output': 0.50},
            'gemini': {'input': 0.50, 'output': 3.00}
        }
    
    def _load_master(self, path: str) -> str:
        """Load V22.2 Master file"""
        if not path or not os.path.exists(path):
            raise ValueError(f"Master file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            system = f.read()
        
        lines = len(system.split('\n'))
        if lines < 47000:
            raise ValueError(f"Master truncated! Expected 47.8K lines, got {lines}")
        
        print(f"✅ V22.2 Master loaded: {lines:,} lines")
        return system
    
    def translate(self, source_text: str, source_lang: str = 'ja', 
                  target_lang: str = 'en') -> Dict:
        """Translate text"""
        
        # Build prompt
        prompt = f"""
Translate from {source_lang.upper()} to {target_lang.upper()}

SOURCE TEXT:
{source_text}

CRITICAL GLOSSARY (535 terms in V22.2):
- ショックキラー = "shock absorber" (NEVER "shock killer")
- 体系表 = "System Chart"
- ストレート取付 = "Inline Mount"

Use all 276 agents and 14 Laws from the V22.2 system.

Output ONLY the translation, no explanations.
"""
        
        # Try Gemini first, fallback to Grok
        try:
            result = self._translate_with_gemini(prompt)
            model = 'gemini-3-flash'
        except:
            result = self._translate_with_grok(prompt)
            model = 'grok-4.1-fast'
        
        # Calculate cost
        cost_usd = (result['tokens_input'] / 1_000_000 * self.pricing[model.split('-')[0]]['input']) + \
                   (result['tokens_output'] / 1_000_000 * self.pricing[model.split('-')[0]]['output'])
        cost_jpy = cost_usd * self.usd_to_jpy
        
        self.total_cost += cost_jpy
        
        return {
            'translation': result['text'],
            'model': model,
            'cost_jpy': cost_jpy,
            'tokens_input': result['tokens_input'],
            'tokens_output': result['tokens_output']
        }
    
    def _translate_with_grok(self, prompt: str) -> Dict:
        """Translate with Grok"""
        if not self.grok_client:
            raise Exception("Grok API key not configured")
        
        response = self.grok_client.chat.completions.create(
            model="grok-4-1-fast-non-reasoning",
            messages=[
                {"role": "system", "content": self.system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        return {
            'text': response.choices[0].message.content.strip(),
            'tokens_input': response.usage.prompt_tokens,
            'tokens_output': response.usage.completion_tokens
        }
    
    def _translate_with_gemini(self, prompt: str) -> Dict:
        """Translate with Gemini"""
        if not self.gemini_api_key:
            raise Exception("Gemini API key not configured")
        
        import google.generativeai as genai
        
        genai.configure(api_key=self.gemini_api_key)
        
        model = genai.GenerativeModel(
            "gemini-3-flash-preview",
            system_instruction=self.system
        )
        
        response = model.generate_content(
            prompt,
            generation_config={'temperature': 0.1}
        )
        
        usage = response.usage_metadata
        
        return {
            'text': response.text.strip(),
            'tokens_input': usage.prompt_token_count,
            'tokens_output': usage.candidates_token_count
        }
