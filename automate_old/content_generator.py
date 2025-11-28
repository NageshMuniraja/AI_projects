"""
Content Idea Generator Module
Generates trending video ideas using OpenAI API
"""
import json
import logging
from datetime import datetime
from openai import OpenAI
from config import Config

logger = logging.getLogger(__name__)

class ContentIdeaGenerator:
    """Generate video content ideas using OpenAI"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.categories = Config.CONTENT_CATEGORIES

    def _parse_json_message(self, content):
        """Safely parse JSON from model message content (strip markdown fences)."""
        if not content:
            raise ValueError("Empty content to parse")
        # Remove triple-backtick fenced blocks if present
        text = content.strip()
        if text.startswith("```"):
            parts = text.split("```", 2)
            if len(parts) >= 2:
                text = parts[1]
                # If the fenced block starts with a language identifier like 'json', drop that first line
                if text.lstrip().startswith(('json', 'json\n')):
                    text = '\n'.join(text.split('\n')[1:])
        # Remove any surrounding backticks and whitespace
        text = text.strip().strip('`').strip()
        return json.loads(text)

    def get_trending_topics(self):
        """Get current trending topics related to kids content and AI"""
        prompt = """
        List 5 current trending topics (as of November 2025) that would make great 
        content for children's educational/entertainment videos. Focus on:
        - Educational topics kids love
        - Trending technology/AI topics explained for kids
        - Viral kids activities
        - Popular children's interests
        - funny AI videos
        
        Return as a simple numbered list.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a children's content strategist who knows trending topics."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )
            
            topics = response.choices[0].message.content.strip()
            logger.info(f"Generated trending topics: {topics}")
            return topics
            
        except Exception as e:
            logger.error(f"Error getting trending topics: {e}")
            return None
    
    def generate_shorts_idea(self):
        """Generate idea for a 60-second short/reel"""
        trending = self.get_trending_topics()
        
        prompt = f"""
        Create ONE engaging video idea for a 60-second short/reel for kids.
        
        Consider these trending topics:
        {trending}
        
        Content should be:
        - Quick, engaging, and visually interesting
        - Educational OR entertaining OR devotional
        - Perfect for kids ages 3-12
        - Can be about: fun facts, quick lessons, funny moments, moral stories, cool experiments
        
        Return a JSON object with:
        {{
            "title": "Catchy title",
            "category": "category name",
            "hook": "Opening line to grab attention",
            "main_idea": "Core concept in one sentence",
            "visual_style": "Description of visual aesthetic",
            "target_age": "Age range",
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative director for viral kids content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=500
            )
            
            idea = self._parse_json_message(response.choices[0].message.content)
            logger.info(f"Generated shorts idea: {idea['title']}")
            return idea
            
        except Exception as e:
            logger.error(f"Error generating shorts idea: {e}")
            return None
    
    def generate_short_video_idea(self):
        """Generate idea for a 3-minute educational video"""
        trending = self.get_trending_topics()
        
        prompt = f"""
        Create ONE engaging video idea for a 3-minute educational video for kids.
        
        Consider these trending topics:
        {trending}
        
        Content should be:
        - Educational with fun presentation
        - Detailed enough for 3 minutes
        - Perfect for kids ages 5-12
        - Topics: learning concepts, science, stories, activities, devotional content
        
        Return a JSON object with:
        {{
            "title": "Educational and engaging title",
            "category": "category name",
            "hook": "Opening that makes kids want to watch",
            "main_concept": "What kids will learn",
            "structure": ["intro", "point1", "point2", "point3", "conclusion"],
            "visual_elements": ["element1", "element2", "element3"],
            "target_age": "Age range",
            "learning_outcome": "What kids take away",
            "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an educational content creator for children."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=700
            )
            
            idea = self._parse_json_message(response.choices[0].message.content)
            logger.info(f"Generated short video idea: {idea['title']}")
            return idea
            
        except Exception as e:
            logger.error(f"Error generating short video idea: {e}")
            return None
    
    def generate_daily_ideas(self):
        """Generate both shorts and short video ideas for the day"""
        logger.info("Generating daily content ideas...")
        
        ideas = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'shorts_reel': self.generate_shorts_idea(),
            'short_video': self.generate_short_video_idea()
        }
        
        # Save ideas to file
        ideas_file = Config.LOG_DIR / f"ideas_{ideas['date']}.json"
        with open(ideas_file, 'w', encoding='utf-8') as f:
            json.dump(ideas, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Daily ideas saved to {ideas_file}")
        return ideas


if __name__ == "__main__":
    # Test the idea generator
    logging.basicConfig(level=logging.INFO)
    Config.create_directories()
    
    generator = ContentIdeaGenerator()
    ideas = generator.generate_daily_ideas()
    print(json.dumps(ideas, indent=2))
