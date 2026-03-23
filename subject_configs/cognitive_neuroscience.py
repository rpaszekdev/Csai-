"""
Subject Configuration - Edit this file to customize for your course.

This is the ONLY file you need to change to use this study assistant
for a different subject. See subject_configs/ for examples.
"""

from pathlib import Path

# ============================================================================
# SUBJECT IDENTITY
# ============================================================================

SUBJECT_NAME = "Cognitive Neuroscience"
SUBJECT_SHORT = "cog_neuro"  # Used for database collection name
COURSE_NAME = "Cognitive Neuroscience"

# ============================================================================
# MATERIALS PATHS - Point these to your lecture files
# ============================================================================

MATERIALS_DIRS = [
    Path.home() / "Desktop" / "lecture_transcripts",
    Path.home() / "Desktop" / "Lectures_pdf",
]

STUDY_GUIDE_PATH = Path.home() / "Desktop" / "STUDY_GUIDE.md"
LECTURES_DIR = Path.home() / "Desktop" / "Lectures_pdf"

# ============================================================================
# LECTURE-TO-PDF MAPPING
# Maps lecture names to their PDF filenames for direct lookup.
# Leave empty if you don't need direct lecture→PDF mapping.
# ============================================================================

LECTURE_PDF_MAP = {
    # "Lecture 1: Neural Signaling": "01-Neural-Signaling.pdf",
    # "Lecture 2: Sensory Systems": "02-Sensory-Systems.pdf",
}

# ============================================================================
# TOPIC-TO-LECTURE REVERSE MAPPING
# Maps individual topics to their parent lecture.
# Leave empty if you don't need this (RAG search still works).
# ============================================================================

TOPIC_LECTURE_MAP = {
    # "Action potentials": "Lecture 1: Neural Signaling",
    # "Resting membrane potential": "Lecture 1: Neural Signaling",
}

# ============================================================================
# STUDY GUIDE - Defines the lecture/topic structure shown in the UI
# ============================================================================

STUDY_GUIDE = {
    "Lecture 1: Neural Signaling": {
        "icon": "🧠",
        "color": "#e94560",
        "topics": [
            "Neurons and glial cells",
            "Resting membrane potential",
            "Action potentials",
            "Synaptic transmission",
        ]
    },
    "Lecture 2: Sensory Systems": {
        "icon": "👁️",
        "color": "#0f3460",
        "topics": [
            "Sensory transduction",
            "Visual processing pathway",
            "Auditory processing",
            "Somatosensory system",
        ]
    },
    "Lecture 3: Motor Systems": {
        "icon": "💪",
        "color": "#4ecca3",
        "topics": [
            "Motor cortex organization",
            "Basal ganglia circuits",
            "Cerebellum and motor learning",
            "Spinal cord reflexes",
        ]
    },
    "Lecture 4: Attention": {
        "icon": "🎯",
        "color": "#ff6b6b",
        "topics": [
            "Selective attention",
            "Divided attention",
            "Neural correlates of attention",
            "Attention disorders (neglect, ADHD)",
        ]
    },
    "Lecture 5: Learning & Memory": {
        "icon": "📝",
        "color": "#45b7d1",
        "topics": [
            "Short-term and working memory",
            "Long-term potentiation (LTP)",
            "Hippocampus and memory consolidation",
            "Types of long-term memory",
        ]
    },
    "Lecture 6: Language": {
        "icon": "💬",
        "color": "#96ceb4",
        "topics": [
            "Broca's and Wernicke's areas",
            "Dual-stream model of language",
            "Language acquisition",
            "Aphasia types",
        ]
    },
    "Lecture 7: Executive Functions": {
        "icon": "🎛️",
        "color": "#dda0dd",
        "topics": [
            "Prefrontal cortex functions",
            "Cognitive control and inhibition",
            "Decision-making and reward",
            "Planning and problem-solving",
        ]
    },
    "Lecture 8: Emotion": {
        "icon": "❤️",
        "color": "#f39c12",
        "topics": [
            "Amygdala and fear processing",
            "Limbic system",
            "Emotion regulation",
            "Emotional memory",
        ]
    },
    "Lecture 9: Consciousness": {
        "icon": "✨",
        "color": "#9b59b6",
        "topics": [
            "Neural correlates of consciousness",
            "Sleep and circadian rhythms",
            "Altered states of consciousness",
            "Theories of consciousness",
        ]
    },
    "Lecture 10: Neuroimaging Methods": {
        "icon": "🔬",
        "color": "#1abc9c",
        "topics": [
            "fMRI and BOLD signal",
            "EEG and event-related potentials",
            "TMS and brain stimulation",
            "Lesion studies and neuropsychology",
        ]
    },
    "Exam Review": {
        "icon": "📋",
        "color": "#f59e0b",
        "topics": [
            "Neural signaling fundamentals",
            "Sensory and motor pathways",
            "Attention and executive function",
            "Memory systems and consolidation",
            "Language processing models",
            "Emotion and limbic system",
            "Neuroimaging methods comparison",
            "Consciousness theories",
        ]
    },
}

# ============================================================================
# TOPIC KEYWORDS - Used for graph generation and smart search
# Set to empty list if your subject doesn't need generated visualizations.
# ============================================================================

TOPIC_KEYWORDS = [
    "neuron", "synapse", "cortex", "hippocampus", "amygdala",
    "prefrontal", "temporal", "parietal", "occipital", "cerebellum",
    "fMRI", "EEG", "ERP", "BOLD", "TMS",
    "action potential", "neurotransmitter", "dopamine", "serotonin",
    "LTP", "memory", "attention", "consciousness",
]

# ============================================================================
# TOPIC-TO-GRAPH MAPPING
# Maps keywords to visualization types. Set to empty dict to disable
# generated graphs (PDF image extraction still works).
# ============================================================================

TOPIC_GRAPH_MAP = {}

# ============================================================================
# FALLBACK SEARCH QUERY
# Used when no specific topic is provided for quiz/search
# ============================================================================

FALLBACK_QUERY = "key concepts cognitive neuroscience brain neural"

# ============================================================================
# CONCEPTS FILE (Optional)
# Path to a markdown file with concept definitions for the concept quiz.
# Set to None to disable the concept quiz feature.
# ============================================================================

CONCEPTS_FILE = None

# ============================================================================
# API TOPICS - Shown in the web UI topic browser
# ============================================================================

API_TOPICS = [
    {"id": "neural_signaling", "name": "Neural Signaling", "icon": "🧠"},
    {"id": "sensory_systems", "name": "Sensory Systems", "icon": "👁️"},
    {"id": "motor_systems", "name": "Motor Systems", "icon": "💪"},
    {"id": "attention", "name": "Attention", "icon": "🎯"},
    {"id": "memory", "name": "Learning & Memory", "icon": "📝"},
    {"id": "language", "name": "Language", "icon": "💬"},
    {"id": "executive_functions", "name": "Executive Functions", "icon": "🎛️"},
    {"id": "emotion", "name": "Emotion", "icon": "❤️"},
    {"id": "consciousness", "name": "Consciousness", "icon": "✨"},
    {"id": "neuroimaging", "name": "Neuroimaging Methods", "icon": "🔬"},
]
