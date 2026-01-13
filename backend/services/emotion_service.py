"""
Emotion Analysis Service using BERT
"""
from transformers import pipeline
from typing import List, Dict, Optional
import torch
from models.emotion import EmotionScores, EmotionProfile, EmotionAnalysisResult
from config.settings import get_settings
import logging

settings = get_settings()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """Emotion analyzer using BERT model"""

    def __init__(self):
        """Initialize the emotion analyzer with BERT model"""
        self.model_name = settings.emotion_model
        self.analyzer = None
        self._load_model()

    def _load_model(self):
        """Load the BERT emotion model"""
        try:
            logger.info(f"Loading emotion model: {self.model_name}")

            # Check if CUDA is available
            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU" if device == 0 else "CPU"
            logger.info(f"Using device: {device_name}")

            # Load the pipeline
            self.analyzer = pipeline(
                "text-classification",
                model=self.model_name,
                return_all_scores=True,
                device=device,
                token=settings.hf_token if settings.hf_token else None
            )

            logger.info("✅ Emotion model loaded successfully!")

        except Exception as e:
            logger.error(f"❌ Failed to load emotion model: {e}")
            raise

    def analyze_text(self, text: str) -> EmotionScores:
        """
        Analyze emotions in a text

        Args:
            text: Text to analyze

        Returns:
            EmotionScores object with emotion probabilities
        """
        if not text or len(text.strip()) == 0:
            # Return neutral emotions for empty text
            return EmotionScores(
                joy=0.0, sadness=0.0, fear=0.0, anger=0.0,
                surprise=0.0, disgust=0.0, neutral=1.0
            )

        # Truncate text if too long (BERT has a max length)
        max_length = 512
        if len(text) > max_length:
            text = text[:max_length]

        try:
            # Get predictions
            results = self.analyzer(text)[0]  # [0] because return_all_scores gives list of lists

            # Convert to EmotionScores
            return EmotionScores.from_bert_output(results)

        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            # Return neutral on error
            return EmotionScores(
                joy=0.0, sadness=0.0, fear=0.0, anger=0.0,
                surprise=0.0, disgust=0.0, neutral=1.0
            )

    def analyze_reviews(self, reviews: List[str]) -> EmotionProfile:
        """
        Analyze multiple reviews and compute average emotion profile

        Args:
            reviews: List of review texts

        Returns:
            EmotionProfile with averaged emotions
        """
        if not reviews:
            # Return neutral profile if no reviews
            neutral_emotions = EmotionScores(
                joy=0.0, sadness=0.0, fear=0.0, anger=0.0,
                surprise=0.0, disgust=0.0, neutral=1.0
            )
            return EmotionProfile.from_base_emotions(neutral_emotions, 0)

        logger.info(f"Analyzing {len(reviews)} reviews...")

        # Analyze each review
        all_emotions = []
        for i, review in enumerate(reviews):
            if i % 10 == 0:
                logger.info(f"  Processed {i}/{len(reviews)} reviews...")

            emotions = self.analyze_text(review)
            all_emotions.append(emotions)

        # Calculate average emotions
        avg_emotions = self._average_emotions(all_emotions)

        # Create emotion profile
        profile = EmotionProfile.from_base_emotions(avg_emotions, len(reviews))

        logger.info(f"✅ Analysis complete. Dominant emotion: {profile.dominant_emotion}")

        return profile

    def _average_emotions(self, emotions_list: List[EmotionScores]) -> EmotionScores:
        """Calculate average of multiple emotion scores"""
        if not emotions_list:
            return EmotionScores(
                joy=0.0, sadness=0.0, fear=0.0, anger=0.0,
                surprise=0.0, disgust=0.0, neutral=1.0
            )

        # Sum all emotions
        total = {
            "joy": 0.0,
            "sadness": 0.0,
            "fear": 0.0,
            "anger": 0.0,
            "surprise": 0.0,
            "disgust": 0.0,
            "neutral": 0.0
        }

        for emotions in emotions_list:
            total["joy"] += emotions.joy
            total["sadness"] += emotions.sadness
            total["fear"] += emotions.fear
            total["anger"] += emotions.anger
            total["surprise"] += emotions.surprise
            total["disgust"] += emotions.disgust
            total["neutral"] += emotions.neutral

        # Calculate average
        count = len(emotions_list)
        avg = {k: v / count for k, v in total.items()}

        return EmotionScores(**avg)

    def analyze_movie_overview(self, overview: str, title: str = "") -> EmotionScores:
        """
        Analyze emotions in a movie overview/description

        Args:
            overview: Movie overview text
            title: Movie title (optional, for logging)

        Returns:
            EmotionScores from the overview
        """
        if title:
            logger.info(f"Analyzing overview for: {title}")

        return self.analyze_text(overview)


# Singleton instance
_analyzer_instance: Optional[EmotionAnalyzer] = None


def get_emotion_analyzer() -> EmotionAnalyzer:
    """Get or create the emotion analyzer singleton"""
    global _analyzer_instance

    if _analyzer_instance is None:
        _analyzer_instance = EmotionAnalyzer()

    return _analyzer_instance
