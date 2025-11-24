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

    def _parse_json_message(self, content):
        """Safely parse JSON from model message content (strip markdown fences)."""
        if not content:
            raise ValueError("Empty content to parse")
        text = content.strip()
        if text.startswith("```"):
            parts = text.split("```", 2)
            if len(parts) >= 2:
                text = parts[1]
                if text.lstrip().startswith(('json', 'json\n')):
                    text = '\n'.join(text.split('\n')[1:])
        text = text.strip().strip('`').strip()
        return json.loads(text)

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
