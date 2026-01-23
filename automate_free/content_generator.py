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
        """Get current trending topics for viral funny content"""
        prompt = """
        List 5 current trending topics (as of November 2025) that would make great 
        viral short-form video content. Focus on:
        - Viral comedy and funny moments
        - Trending memes and internet culture
        - Relatable life situations that make people laugh
        - Unexpected plot twists and surprises
        - Mind-blowing facts and life hacks
        - Satisfying and oddly satisfying content
        - Topics that work for all ages (clean humor)
        
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
        Create ONE highly engaging and FUNNY video idea for a 60-second viral short/reel.
        
        Consider these trending topics:
        {trending}
        
        Content should be:
        - FUNNY and entertaining (primary focus)
        - Quick, engaging, and visually captivating
        - Relatable to broad audiences (ages 10+)
        - Can include: comedy, unexpected twists, funny facts, life hacks, satisfying moments, plot twists
        - Should make people laugh, smile, or say "wow!"
        - Clean humor (family-friendly but not just for little kids)
        
        Return a JSON object with:
        {{
            "title": "Catchy and intriguing title",
            "category": "category name",
            "hook": "Opening line that grabs attention immediately",
            "main_idea": "Core concept in one sentence",
            "visual_style": "Description of visual aesthetic and mood",
            "target_age": "Age range (e.g., 10+, 13+, All ages)",
            "humor_type": "Type of humor (e.g., situational, slapstick, clever, relatable)",
            "music_mood": "Background music mood (e.g., upbeat, suspenseful, energetic, chill)",
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
        """Generate idea for a 3-minute entertaining/educational video"""
        trending = self.get_trending_topics()
        
        prompt = f"""
        Create ONE engaging video idea for a 3-minute entertaining video.
        
        Consider these trending topics:
        {trending}
        
        Content should be:
        - Entertaining with educational or inspirational elements
        - Engaging enough to hold attention for 3 minutes
        - Appeals to broad audiences (ages 10+)
        - Can be: funny stories, amazing facts, life lessons, how-to guides, motivational content
        - Should be fun and engaging, not boring
        
        Return a JSON object with:
        {{
            "title": "Engaging and click-worthy title",
            "category": "category name",
            "hook": "Opening that makes viewers want to watch",
            "main_concept": "Core message or entertainment value",
            "structure": ["intro", "point1", "point2", "point3", "conclusion"],
            "visual_elements": ["element1", "element2", "element3"],
            "target_age": "Age range",
            "learning_outcome": "What viewers take away or feel",
            "music_mood": "Background music mood throughout",
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
