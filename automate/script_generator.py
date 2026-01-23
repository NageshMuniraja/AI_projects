"""
Script Generator Module
Generates detailed video scripts from content ideas using OpenAI
"""
import json
import logging
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)

class ScriptGenerator:
    """Generate video scripts using OpenAI"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)

    '''
    def _parse_json_message(self, content):
        """Safely parse JSON from model message content (strip markdown fences).

        This function attempts multiple recovery strategies when the model returns
        imperfect JSON (unescaped newlines, extra text, or code fences). It will:
        - Strip surrounding triple-backtick fences and optional language tags
        - Extract the first {...} or [...] JSON block if present
        - Escape raw control characters (newline, tab, carriage) and remove other control chars
        - Try json.loads on progressively cleaned text
        """
        if not content:
            raise ValueError("Empty content to parse")
        import re
        text = content.strip()
        # Remove surrounding code fences if present
        if text.startswith("```"):
            parts = text.split("```", 2)
            if len(parts) >= 2:
                text = parts[1]
                # Remove leading language tag like ```json
                if text.lstrip().startswith(('json', 'json\n')):
                    text = '\n'.join(text.split('\n')[1:])
        text = text.strip().strip('`').strip()

        # Try straightforward parse first
        try:
            return json.loads(text)
        except Exception:
            pass

        # Try to extract a JSON object/array substring
        # Look for first {...} or [...] block
        obj_match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        candidate = obj_match.group(1) if obj_match else text

        # Replace raw newlines, tabs, carriage returns with escaped equivalents
        # and remove other control characters that break JSON parsing
        def _sanitize_raw(s: str) -> str:
            # Escape common whitespace characters
            s = s.replace('\\r', '\\r').replace('\\n', '\\n')
            s = s.replace('\r', '\\r').replace('\n', '\\n').replace('\t', '\\t')
            # Remove control characters except escaped sequences now present
            s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', s)
            return s

        candidate_clean = _sanitize_raw(candidate)

        try:
            return json.loads(candidate_clean)
        except Exception as e:
            # Last-ditch attempt: try to fix common issues like trailing commas
            try:
                # Remove trailing commas before } or ]
                candidate_no_trailing = re.sub(r',\s*([}\]])', r'\1', candidate_clean)
                return json.loads(candidate_no_trailing)
            except Exception:
                raise ValueError(f"Failed to parse JSON from model output: {e}\n---raw content---\n{text}")
    '''
    def _parse_json_message(self, content: str):
        """
        Robust JSON parser for model outputs.

        Tries (in order):
        - strip BOM and code fences
        - direct json.loads
        - extract first balanced {...} or [...] block and try json.loads
        - ast.literal_eval (accept Python-style quotes/True/None)
        - conservative fixes (single->double quotes, True/False/None -> true/false/null, remove trailing commas) then json.loads
        Raises ValueError with debug info if all attempts fail.
        """
        if not content:
            raise ValueError("Empty content to parse")

        import re, ast, json

        raw = content

        # Remove BOM if present
        try:
            raw = raw.encode('utf-8').decode('utf-8-sig')
        except Exception:
            # ignore if decode fails
            pass

        # Trim whitespace and fences
        raw = raw.strip()
        if raw.startswith("```"):
            # remove first code fence block (```json ... ``` or ``` ... ```)
            parts = raw.split("```", 2)
            if len(parts) >= 2:
                raw = parts[1]
                # remove optional leading language token like "json"
                if raw.lstrip().lower().startswith("json"):
                    raw = "\n".join(raw.split("\n")[1:])
        raw = raw.strip().strip('`').strip()

        # Quick direct JSON attempt
        try:
            return json.loads(raw)
        except Exception:
            pass

        # Extract first balanced JSON block (object or array)
        def _extract_first_json_block(s: str) -> str:
            start_idx = None
            for i, ch in enumerate(s):
                if ch in ('{', '['):
                    start_idx = i
                    break
            if start_idx is None:
                return s
            pairs = {'{': '}', '[': ']'}
            stack = []
            i = start_idx
            while i < len(s):
                ch = s[i]
                if ch in ('{', '['):
                    stack.append(ch)
                elif ch in ('}', ']'):
                    if not stack:
                        return s[start_idx:i+1]
                    last = stack[-1]
                    if pairs[last] == ch:
                        stack.pop()
                        if not stack:
                            return s[start_idx:i+1]
                i += 1
            return s[start_idx:]

        candidate = _extract_first_json_block(raw).strip()

        # Try json.loads on candidate
        try:
            return json.loads(candidate)
        except Exception:
            pass

        # Try ast.literal_eval (accepts single quotes, True/False/None)
        try:
            parsed = ast.literal_eval(candidate)
            return parsed
        except Exception:
            pass

        # Conservative fixes then try json.loads
        def _conservative_fix(s: str) -> str:
            # Normalize newlines
            s = s.replace('\r\n', '\n').replace('\r', '\n').strip()
            # Convert python literals to JSON
            s = re.sub(r'\bNone\b', 'null', s)
            s = re.sub(r'\bTrue\b', 'true', s)
            s = re.sub(r'\bFalse\b', 'false', s)
            # Remove trailing commas
            s = re.sub(r',\s*([}\]])', r'\1', s)
            # Replace smart quotes with standard quotes
            s = s.replace('“', '"').replace('”', '"').replace("’", "'")
            # Replace single-quotes with double-quotes conservatively
            if '"' not in s:
                s = s.replace("'", '"')
            else:
                s = re.sub(r"(?<=[:\s\[,])'([^']*)'(?=[,\]\}\s])", r'"\1"', s)
            return s

        candidate_fixed = _conservative_fix(candidate)
        try:
            return json.loads(candidate_fixed)
        except Exception as e:
            # Give helpful debug in exception
            raise ValueError(
                f"Failed to parse JSON from model output after multiple attempts: {e}\n"
                f"---raw content---\n{content}\n"
                f"---extracted candidate---\n{candidate}\n"
                f"---candidate_fixed---\n{candidate_fixed}"
            )
    def generate_shorts_script(self, idea):
        """Generate script for 60-second short/reel"""
        prompt = f"""
        Create a detailed 60-second video script for kids based on this idea:
        
        Title: {idea['title']}
        Category: {idea['category']}
        Hook: {idea['hook']}
        Main Idea: {idea['main_idea']}
        Target Age: {idea['target_age']}
        
        The script must:
        - Be EXACTLY 60 seconds when read at natural pace (150-160 words)
        - Start with an attention-grabbing hook
        - Be energetic and engaging for kids
        - Use simple language
        - Include natural pauses [PAUSE]
        - Include emphasis markers *word* for important words
        - End with a call-to-action
        
        Return a JSON object with:
        {{
            "script": "Full script text with markers",
            "duration": 60,
            "word_count": number,
            "visual_prompts": ["prompt1", "prompt2", "prompt3", "prompt4"],
            "text_overlays": ["text1", "text2", "text3"],
            "background_music": "music mood description"
        }}
        
        Visual prompts should describe what to show at key moments (for AI video generation).
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a script writer for viral kids content. Write engaging, energetic scripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1000
            )
            
            script_data = self._parse_json_message(response.choices[0].message.content)
            logger.info(f"Generated shorts script: {script_data['word_count']} words")
            return script_data
            
        except Exception as e:
            logger.error(f"Error generating shorts script: {e}")
            return None
    
    def generate_short_video_script(self, idea):
        """Generate script for 3-minute educational video"""
        prompt = f"""
        Create a detailed 3-minute educational video script for kids based on this idea:
        
        Title: {idea['title']}
        Category: {idea['category']}
        Hook: {idea['hook']}
        Main Concept: {idea['main_concept']}
        Structure: {idea['structure']}
        Target Age: {idea['target_age']}
        Learning Outcome: {idea['learning_outcome']}
        
        The script must:
        - Be EXACTLY 3 minutes when read at natural pace (450-480 words)
        - Have clear sections: INTRO, MAIN CONTENT (3 points), CONCLUSION
        - Be educational but fun and engaging
        - Use simple language kids understand
        - Include natural pauses [PAUSE]
        - Include emphasis markers *word* for important words
        - Include questions to engage kids
        - End with a memorable takeaway
        
        Return a JSON object with:
        {{
            "script": "Full script text with section markers and pauses",
            "duration": 180,
            "word_count": number,
            "sections": [
                {{"name": "intro", "script": "intro text", "duration": 30}},
                {{"name": "point1", "script": "point1 text", "duration": 35}},
                {{"name": "point2", "script": "point2 text", "duration": 35}},
                {{"name": "point3", "script": "point3 text", "duration": 35}},
                {{"name": "conclusion", "script": "conclusion text", "duration": 45}}
            ],
            "visual_prompts": ["prompt1", "prompt2", "prompt3", "prompt4", "prompt5", "prompt6"],
            "text_overlays": ["text1", "text2", "text3", "text4"],
            "background_music": "music mood description"
        }}
        
        Visual prompts should describe key scenes for AI video generation.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an educational script writer for children's content. Make learning fun and engaging."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            script_data = self._parse_json_message(response.choices[0].message.content)
            logger.info(f"Generated short video script: {script_data['word_count']} words")
            return script_data
            
        except Exception as e:
            logger.error(f"Error generating short video script: {e}")
            return None
    
    def generate_visual_descriptions(self, script_data, video_type="shorts"):
        """Generate detailed visual descriptions for video generation"""
        script = script_data['script']
        
        prompt = f"""
        Based on this {video_type} script for kids, create detailed visual descriptions for AI video generation.
        
        Script:
        {script}
        
        Generate 4-6 detailed visual prompts that:
        - Describe colorful, engaging scenes kids will love
        - Are specific enough for AI video generation (Runway/Pika)
        - Match the script narrative
        - Include visual style keywords: "vibrant colors", "3D animation style", "bright lighting", etc.
        - Are kid-friendly and educational
        
        Return a JSON object with:
        {{
            "visual_prompts": [
                {{"timestamp": "0-15s", "prompt": "detailed visual description", "style": "animation/realistic/3D"}},
                {{"timestamp": "16-30s", "prompt": "detailed visual description", "style": "animation/realistic/3D"}},
                ...
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a visual director for children's content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            visuals = self._parse_json_message(response.choices[0].message.content)
            logger.info(f"Generated {len(visuals['visual_prompts'])} visual prompts")
            return visuals
            
        except Exception as e:
            logger.error(f"Error generating visual descriptions: {e}")
            return None
    
    def generate_metadata(self, idea, script_data, video_type="shorts"):
        """Generate title, description, and tags for social media"""
        prompt = f"""
        Create optimized metadata for a {video_type} video for YouTube and Instagram.
        
        Idea: {idea['title']}
        Category: {idea['category']}
        Script summary: {script_data['script'][:200]}...
        
        Generate:
        1. YouTube-optimized title (under 60 characters, includes keywords)
        2. YouTube description (3-4 sentences, engaging, includes hashtags)
        3. Instagram caption (engaging, includes emojis, hashtags)
        4. 10-15 relevant hashtags
        
        Return a JSON object with:
        {{
            "youtube_title": "title",
            "youtube_description": "description",
            "youtube_tags": ["tag1", "tag2", ...],
            "instagram_caption": "caption with emojis",
            "hashtags": ["#tag1", "#tag2", ...]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a social media manager specializing in kids content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            metadata = self._parse_json_message(response.choices[0].message.content)
            logger.info("Generated video metadata")
            return metadata
            
        except Exception as e:
            logger.error(f"Error generating metadata: {e}")
            return None


if __name__ == "__main__":
    # Test the script generator
    logging.basicConfig(level=logging.INFO)
    
    # Example idea for testing
    test_idea = {
        "title": "Why Do Leaves Change Color? 🍂",
        "category": "kids learning",
        "hook": "Have you ever wondered why leaves turn red and yellow?",
        "main_idea": "Leaves change color because of hidden pigments revealed when chlorophyll breaks down",
        "target_age": "6-10"
    }
    
    generator = ScriptGenerator()
    script = generator.generate_shorts_script(test_idea)
    print(json.dumps(script, indent=2))
