import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import logging
import time

# Load environment variables from .env file
load_dotenv()

class HealthcareNLPProcessor:
    def __init__(self):
        """
        Initialize the NLP processor with OpenAI API key from environment
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
        
        self.client = OpenAI(api_key=self.api_key)
        
        # Healthcare-specific intent patterns for pattern matching
        self.intent_patterns = {
            'TPA_INQUIRY': [
                r'\b(tpa|third party administrator|administrator)\b',
                r'\b(insurance|coverage|benefits)\b',
                r'\b(provider network|network)\b'
            ],
            'CARD_TRENDS': [
                r'\b(card|spending|trends|usage|patterns)\b',
                r'\b(monthly|quarterly|annual|costs)\b',
                r'\b(analysis|breakdown|summary)\b'
            ],
            'CLAIM_STATUS': [
                r'\b(claim|claims|status|approval|denial)\b',
                r'\b(pending|processing|approved|denied)\b',
                r'\b(reimbursement|payment)\b'
            ],
            'FINANCIAL_REPORT': [
                r'\b(report|financial|cost|expense|budget)\b',
                r'\b(revenue|profit|loss|margin)\b',
                r'\b(comparison|benchmark)\b'
            ],
            'ANOMALY_DETECTION': [
                r'\b(unusual|abnormal|anomaly|suspicious)\b',
                r'\b(alert|flag|warning|issue)\b',
                r'\b(fraud|error|mistake)\b'
            ]
        }
        
        print("✅ Healthcare NLP Processor initialized successfully!")
        print(f"🔑 OpenAI API Key loaded: {'Yes' if self.api_key else 'No'}")
    
    def preprocess_query(self, query: str) -> str:
        """Clean and standardize the input query"""
        query = query.lower().strip()
        
        healthcare_replacements = {
            'tpas': 'third party administrators',
            'hsa': 'health savings account',
            'fsa': 'flexible spending account',
            'eob': 'explanation of benefits',
            'copay': 'co-payment',
            'deductible': 'deductible amount',
            'claims': 'insurance claims',
            'providers': 'healthcare providers'
        }
        
        for term, replacement in healthcare_replacements.items():
            query = re.sub(rf'\b{term}\b', replacement, query)
        
        query = re.sub(r'\s+', ' ', query)
        query = re.sub(r'[^\w\s\?\.,!-]', '', query)
        
        return query.strip()
    
    def classify_intent_with_patterns(self, query: str) -> Dict:
        """Pattern-based intent classification for backup/validation"""
        pattern_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query, re.IGNORECASE))
                score += matches
            pattern_scores[intent] = score
        
        if max(pattern_scores.values()) > 0:
            best_intent = max(pattern_scores, key=pattern_scores.get)
            confidence = min(pattern_scores[best_intent] * 0.3, 0.9)
            return {
                'intent': best_intent,
                'confidence': confidence,
                'method': 'pattern_matching'
            }
        
        return {
            'intent': 'UNKNOWN',
            'confidence': 0.0,
            'method': 'pattern_matching'
        }
    
    def classify_intent_with_openai(self, query: str, retry_count: int = 3) -> Dict:
        """
        Use OpenAI GPT for advanced intent classification with robust error handling
        """
        # Simplified prompt that's more likely to return valid JSON
        prompt = f"""Classify this healthcare query into one intent:

Query: "{query}"

Intents: TPA_INQUIRY, CARD_TRENDS, CLAIM_STATUS, FINANCIAL_REPORT, ANOMALY_DETECTION, USER_ACCOUNT, GENERAL_INFO

Response format:
{{"intent": "INTENT_NAME", "confidence": 0.9, "reasoning": "why"}}"""
        
        for attempt in range(retry_count):
            try:
                print(f"🔄 OpenAI API attempt {attempt + 1}/{retry_count}")
                
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Using more reliable model
                    messages=[
                        {"role": "system", "content": "You are a healthcare intent classifier. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,  # Reduced token limit
                    temperature=0.1,
                    timeout=30  # Add timeout
                )
                
                result_text = response.choices[0].message.content.strip()
                
                print(f"📝 Raw API Response: '{result_text}'")
                
                if not result_text:
                    raise ValueError("Empty response from OpenAI API")
                
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                    print(f"🔍 Extracted JSON: '{json_text}'")
                    classification = json.loads(json_text)
                else:
                    # Fallback: try parsing the entire response
                    classification = json.loads(result_text)
                
                # Validate required fields
                if 'intent' not in classification:
                    raise ValueError("Missing 'intent' field in response")
                
                classification['method'] = 'openai_gpt'
                classification.setdefault('confidence', 0.8)
                classification.setdefault('reasoning', 'OpenAI classification')
                
                print(f"✅ OpenAI classification successful: {classification['intent']}")
                return classification
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse Error (attempt {attempt + 1}): {str(e)}")
                print(f"📄 Response content: '{result_text}'")
                
                # Try to extract intent from non-JSON response
                if 'result_text' in locals():
                    intent_match = re.search(r'(TPA_INQUIRY|CARD_TRENDS|CLAIM_STATUS|FINANCIAL_REPORT|ANOMALY_DETECTION|USER_ACCOUNT|GENERAL_INFO)', result_text, re.IGNORECASE)
                    if intent_match:
                        return {
                            'intent': intent_match.group(1).upper(),
                            'confidence': 0.6,
                            'method': 'openai_gpt',
                            'reasoning': 'Extracted from non-JSON response'
                        }
                
            except Exception as e:
                print(f"❌ OpenAI API Error (attempt {attempt + 1}): {str(e)}")
                
            # Wait before retry
            if attempt < retry_count - 1:
                print(f"⏳ Waiting 2 seconds before retry...")
                time.sleep(2)
        
        print("❌ All OpenAI attempts failed, falling back to pattern matching")
        return {
            'intent': 'UNKNOWN',
            'confidence': 0.0,
            'method': 'openai_gpt_failed',
            'error': 'All attempts failed'
        }
    
    def extract_entities(self, query: str) -> List[Dict]:
        """Extract healthcare-specific entities from the query"""
        entities = []
        
        healthcare_patterns = {
            'TPA_NAME': r'\b([A-Z][a-z]+ (Healthcare|Insurance|Benefits|TPA))\b',
            'AMOUNT': r'\$[\d,]+\.?\d*',
            'PERCENTAGE': r'\d+\.?\d*%',
            'DATE_RANGE': r'(last|past|previous) \d+ (days?|weeks?|months?|quarters?|years?)',
            'CARD_TYPE': r'\b(debit|credit|HSA|FSA) cards?\b',
            'DEPARTMENT': r'\b(cardiology|oncology|emergency|primary care|specialist)\b',
            'TIME_PERIOD': r'\b(today|yesterday|this week|last week|this month|last month|this quarter|last quarter|this year|last year)\b'
        }
        
        for entity_type, pattern in healthcare_patterns.items():
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'type': entity_type,
                    'confidence': 0.9,
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    def get_fallback_enhancement(self, query: str, intent: str) -> Dict:
        """
        Fallback query enhancement when OpenAI is not available
        """
        enhancements = {
            'TPA_INQUIRY': {
                'enhanced_query': f"Show TPA information including approval rates and status for: {query}",
                'required_tables': ['tpa_info', 'claims'],
                'suggested_filters': ['tpa_status = active'],
                'aggregation_needed': True
            },
            'CARD_TRENDS': {
                'enhanced_query': f"Show card spending trends with monthly breakdown for: {query}",
                'required_tables': ['card_transactions', 'patient_data'],
                'suggested_filters': ['transaction_date >= last_month'],
                'aggregation_needed': True
            },
            'CLAIM_STATUS': {
                'enhanced_query': f"Show claim status and processing information for: {query}",
                'required_tables': ['claims', 'claim_status'],
                'suggested_filters': ['claim_date >= last_30_days'],
                'aggregation_needed': False
            },
            'FINANCIAL_REPORT': {
                'enhanced_query': f"Generate financial analysis and cost breakdown for: {query}",
                'required_tables': ['financial_data', 'cost_centers'],
                'suggested_filters': ['report_period >= last_quarter'],
                'aggregation_needed': True
            }
        }
        
        return enhancements.get(intent, {
            'enhanced_query': query,
            'required_tables': ['unknown'],
            'suggested_filters': [],
            'aggregation_needed': False
        })
    
    def process_natural_query(self, query: str, user_context: Dict) -> Dict:
        """Complete NLP processing pipeline with robust error handling"""
        processing_start = datetime.now()
        
        print(f"\n🏥 Processing Healthcare Query")
        print(f"📝 Original Query: '{query}'")
        
        # Step 1: Preprocess and clean query
        cleaned_query = self.preprocess_query(query)
        print(f"🧹 Cleaned Query: '{cleaned_query}'")
        
        # Step 2: Pattern-based classification (always works)
        pattern_result = self.classify_intent_with_patterns(cleaned_query)
        print(f"🔍 Pattern Classification: {pattern_result['intent']} (confidence: {pattern_result['confidence']:.2f})")
        
        # Step 3: OpenAI-based classification (with fallback)
        openai_result = self.classify_intent_with_openai(cleaned_query)
        
        # Step 4: Choose best classification result
        if openai_result.get('confidence', 0) > 0.7 and 'error' not in openai_result:
            final_intent = openai_result
            print(f"✅ Using OpenAI result: {final_intent['intent']}")
        elif pattern_result['confidence'] > 0.3:
            final_intent = pattern_result
            print(f"✅ Using Pattern result: {final_intent['intent']}")
        else:
            final_intent = {'intent': 'GENERAL_INFO', 'confidence': 0.5, 'method': 'fallback'}
            print(f"✅ Using Fallback result: {final_intent['intent']}")
        
        # Step 5: Extract entities
        entities = self.extract_entities(cleaned_query)
        if entities:
            print(f"🏷️  Entities Found: {[e['text'] + ' (' + e['type'] + ')' for e in entities]}")
        else:
            print("🏷️  No entities found")
        
        # Step 6: Enhanced query (with fallback)
        enhanced_query = self.get_fallback_enhancement(cleaned_query, final_intent['intent'])
        print(f"🚀 Enhanced Query: '{enhanced_query.get('enhanced_query', cleaned_query)}'")
        
        processing_time = (datetime.now() - processing_start).total_seconds()
        print(f"⏱️  Processing completed in {processing_time:.2f} seconds")
        
        return {
            'original_query': query,
            'cleaned_query': cleaned_query,
            'enhanced_query': enhanced_query.get('enhanced_query', cleaned_query),
            'intent': final_intent['intent'],
            'intent_confidence': final_intent.get('confidence', 0),
            'intent_reasoning': final_intent.get('reasoning', 'Pattern matching'),
            'entities': entities,
            'required_tables': enhanced_query.get('required_tables', []),
            'suggested_filters': enhanced_query.get('suggested_filters', []),
            'processing_time_seconds': processing_time,
            'processing_timestamp': datetime.now().isoformat(),
            'classification_method': final_intent.get('method', 'unknown'),
            'openai_status': 'success' if openai_result.get('confidence', 0) > 0.7 else 'failed_or_low_confidence'
        }

# Interactive test function with better error handling
def interactive_test():
    """Interactive testing with comprehensive error handling"""
    try:
        nlp_processor = HealthcareNLPProcessor()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure you have:")
        print("   1. Created a .env file with OPENAI_API_KEY=your-api-key")
        print("   2. Installed required packages: pip install openai python-dotenv")
        return
    
    user_context = {
        'user_id': 'user_123',
        'role': 'healthcare_provider',
        'organization_id': 'hospital_001',
        'access_level': 'advanced'
    }
    
    print("\n🏥 Healthcare Fintech NLP Processor - Interactive Mode")
    print("=" * 60)
    print("💡 Type your healthcare queries or 'quit' to exit")
    print("🛡️  This version includes robust error handling and fallbacks")
    print("-" * 60)
    
    while True:
        try:
            query = input("\n🔍 Enter your query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not query:
                print("❌ Please enter a valid query")
                continue
            
            result = nlp_processor.process_natural_query(query, user_context)
            
            print(f"\n📊 RESULTS:")
            print(f"✅ Final Intent: {result['intent']} (confidence: {result['intent_confidence']:.2f})")
            print(f"🔧 Method Used: {result['classification_method']}")
            print(f"📋 Required Tables: {result['required_tables']}")
            print(f"🔍 Suggested Filters: {result['suggested_filters']}")
            print(f"🤖 OpenAI Status: {result['openai_status']}")
            print("-" * 60)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error processing query: {str(e)}")
            print("🔄 Continuing with next query...")

if __name__ == "__main__":
    interactive_test()
