"""
Emotion data models for CineFeels
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class EmotionScores(BaseModel):
    """Base emotion scores from BERT model"""
    joy: float = Field(ge=0.0, le=1.0, description="Joy emotion score")
    sadness: float = Field(ge=0.0, le=1.0, description="Sadness emotion score")
    fear: float = Field(ge=0.0, le=1.0, description="Fear emotion score")
    anger: float = Field(ge=0.0, le=1.0, description="Anger emotion score")
    surprise: float = Field(ge=0.0, le=1.0, description="Surprise emotion score")
    disgust: float = Field(ge=0.0, le=1.0, description="Disgust emotion score")
    neutral: float = Field(ge=0.0, le=1.0, description="Neutral emotion score")

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return {
            "joy": self.joy,
            "sadness": self.sadness,
            "fear": self.fear,
            "anger": self.anger,
            "surprise": self.surprise,
            "disgust": self.disgust,
            "neutral": self.neutral
        }

    @classmethod
    def from_bert_output(cls, bert_results: List[Dict]) -> "EmotionScores":
        """Create EmotionScores from BERT pipeline output"""
        scores = {item['label']: item['score'] for item in bert_results}
        return cls(**scores)


class EmotionProfile(BaseModel):
    """Emotion profile for a movie"""
    base_emotions: EmotionScores = Field(description="Base 7 emotion scores")

    # CineFeels custom emotions
    thrill: float = Field(ge=0.0, le=1.0, description="Thrill level (fear + surprise)")
    romance: float = Field(ge=0.0, le=1.0, description="Romance level (joy)")
    inspiration: float = Field(ge=0.0, le=1.0, description="Inspiration level (joy + surprise)")
    humor: float = Field(ge=0.0, le=1.0, description="Humor level (joy)")

    # Metadata
    reviews_analyzed: int = Field(description="Number of reviews analyzed")
    dominant_emotion: str = Field(description="The dominant emotion")

    @classmethod
    def from_base_emotions(cls, base_emotions: EmotionScores, reviews_count: int) -> "EmotionProfile":
        """Create EmotionProfile from base emotions"""
        # Calculate CineFeels custom emotions
        thrill = (base_emotions.fear + base_emotions.surprise) / 2
        romance = base_emotions.joy  # Can be refined with keywords later
        inspiration = (base_emotions.joy + base_emotions.surprise) / 2
        humor = base_emotions.joy  # Can be refined with keywords later

        # Find dominant emotion
        emotion_dict = base_emotions.to_dict()
        dominant_emotion = max(emotion_dict, key=emotion_dict.get)

        return cls(
            base_emotions=base_emotions,
            thrill=thrill,
            romance=romance,
            inspiration=inspiration,
            humor=humor,
            reviews_analyzed=reviews_count,
            dominant_emotion=dominant_emotion
        )


class MovieEmotion(BaseModel):
    """Movie with emotion profile"""
    movie_id: int = Field(description="TMDB movie ID")
    title: str = Field(description="Movie title")
    emotion_profile: EmotionProfile = Field(description="Emotion profile")

    class Config:
        json_schema_extra = {
            "example": {
                "movie_id": 550,
                "title": "Fight Club",
                "emotion_profile": {
                    "base_emotions": {
                        "joy": 0.15,
                        "sadness": 0.20,
                        "fear": 0.35,
                        "anger": 0.45,
                        "surprise": 0.30,
                        "disgust": 0.25,
                        "neutral": 0.10
                    },
                    "thrill": 0.325,
                    "romance": 0.15,
                    "inspiration": 0.225,
                    "humor": 0.15,
                    "reviews_analyzed": 25,
                    "dominant_emotion": "anger"
                }
            }
        }


class EmotionAnalysisResult(BaseModel):
    """Result of emotion analysis for a single text"""
    text_snippet: str = Field(description="First 100 chars of analyzed text")
    emotions: EmotionScores = Field(description="Detected emotions")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall confidence")

    @classmethod
    def from_bert_output(cls, text: str, bert_results: List[Dict]) -> "EmotionAnalysisResult":
        """Create from BERT output"""
        emotions = EmotionScores.from_bert_output(bert_results)

        # Confidence is the highest score
        confidence = max(item['score'] for item in bert_results)

        return cls(
            text_snippet=text[:100],
            emotions=emotions,
            confidence=confidence
        )
