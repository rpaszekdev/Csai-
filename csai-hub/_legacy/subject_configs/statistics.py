"""
Subject Configuration — Statistics (example)

Copy this to ../subject_config.py and edit the paths to match your setup.
"""

from pathlib import Path

SUBJECT_NAME = "Statistics"
SUBJECT_SHORT = "stats"
COURSE_NAME = "Statistics II"

MATERIALS_DIRS = [
    Path.home() / "Desktop" / "lecture_transcripts",
    Path.home() / "Desktop" / "Lectures_pdf",
]

STUDY_GUIDE_PATH = Path.home() / "Desktop" / "STUDY_GUIDE.md"
LECTURES_DIR = Path.home() / "Desktop" / "Lectures_pdf"

LECTURE_PDF_MAP = {
    "Lecture 1: Introduction and Probability": "1-Intro and Probability.pdf",
    "Lecture 2: Sampling Theory": "2-Sampling-Theory.pdf",
    "Lecture 3: Hypothesis Testing & Correlation": "3-Hypothesis-Testing.pdf",
    "Lecture 4: Correlation (continued)": "4-Correlation.pdf",
    "Lecture 5: Linear Regression": "5-Linear-Regression.pdf",
    "Lecture 6: Regression Assumptions": "6-Regression-Assumptions.pdf",
    "Lecture 7: Multiple Regression": "7-Multiple-Regression.pdf",
    "Lecture 8: Interactions": "8-Interactions.pdf",
    "Lecture 9: Categorical Variables": "9-Categorical-Variables.pdf",
    "Lecture 10: Polynomial Regression": "10-Polynomial-Regression.pdf",
    "Lecture 11: Mixed Models": "11-Mixed-Models.pdf",
    "Lecture 12: Growth Curve Modeling": "12-Growth-Curves.pdf",
}

TOPIC_LECTURE_MAP = {
    "Basics of Probability": "Lecture 1: Introduction and Probability",
    "Central limit theorem": "Lecture 2: Sampling Theory",
    "Hypothesis testing": "Lecture 3: Hypothesis Testing & Correlation",
    "Correlation": "Lecture 4: Correlation (continued)",
    "Linear regression": "Lecture 5: Linear Regression",
    "Regression assumptions": "Lecture 6: Regression Assumptions",
    "Multiple regression": "Lecture 7: Multiple Regression",
    "Interactions": "Lecture 8: Interactions",
    "Categorical variables": "Lecture 9: Categorical Variables",
    "Polynomial regression": "Lecture 10: Polynomial Regression",
    "Mixed models": "Lecture 11: Mixed Models",
    "Growth curve modeling": "Lecture 12: Growth Curve Modeling",
}

STUDY_GUIDE = {
    "Lecture 1: Introduction and Probability": {
        "icon": "🎲",
        "color": "#e94560",
        "topics": [
            "Basics of Probability",
            "Relationship between models and data",
            "Distribution functions in R",
            "Normal distribution characteristics",
        ]
    },
    "Lecture 2: Sampling Theory": {
        "icon": "📊",
        "color": "#0f3460",
        "topics": [
            "Basics of sampling theory",
            "Types of sampling methods",
            "Central limit theorem",
            "Standard error and confidence intervals",
        ]
    },
    "Lecture 3: Hypothesis Testing & Correlation": {
        "icon": "🔬",
        "color": "#4ecca3",
        "topics": [
            "Null and alternative hypotheses",
            "P-values and alpha levels",
            "Type I and Type II errors",
            "Covariance and correlation",
        ]
    },
    "Lecture 4: Correlation (continued)": {
        "icon": "📈",
        "color": "#ff6b6b",
        "topics": [
            "Pearson, Spearman, Kendall correlation",
            "Partial and semi-partial correlation",
        ]
    },
    "Lecture 5: Linear Regression": {
        "icon": "📉",
        "color": "#45b7d1",
        "topics": [
            "Simple linear regression",
            "R-squared",
            "F-test and t-test",
        ]
    },
    "Lecture 6: Regression Assumptions": {
        "icon": "✅",
        "color": "#96ceb4",
        "topics": [
            "Linearity, homoscedasticity, normality",
            "Outlier detection",
        ]
    },
    "Lecture 7: Multiple Regression": {
        "icon": "🔢",
        "color": "#dda0dd",
        "topics": [
            "Multiple predictors",
            "Adjusted R-squared",
            "Model comparison (AIC)",
        ]
    },
    "Lecture 8: Interactions": {
        "icon": "🔀",
        "color": "#f39c12",
        "topics": [
            "Interaction effects",
            "Simple slopes analysis",
        ]
    },
    "Lecture 9: Categorical Variables": {
        "icon": "🏷️",
        "color": "#9b59b6",
        "topics": [
            "Dummy coding",
            "Effects coding",
            "Contrast coding",
        ]
    },
    "Lecture 10: Polynomial Regression": {
        "icon": "〰️",
        "color": "#1abc9c",
        "topics": [
            "Polynomial terms",
            "Interpreting curved relationships",
        ]
    },
    "Lecture 11: Mixed Models": {
        "icon": "🔄",
        "color": "#3498db",
        "topics": [
            "Random intercepts and slopes",
            "Marginal vs conditional R-squared",
        ]
    },
    "Lecture 12: Growth Curve Modeling": {
        "icon": "📈",
        "color": "#e74c3c",
        "topics": [
            "Growth curve models",
            "Interpreting longitudinal data",
        ]
    },
}

TOPIC_KEYWORDS = [
    "normal", "distribution", "regression", "linear", "correlation",
    "hypothesis", "p-value", "t-test", "confidence", "interval",
    "anova", "variance", "chi-square", "probability", "sampling",
    "central limit", "standard error", "binomial", "poisson",
]

TOPIC_GRAPH_MAP = {
    "normal": ["normal_distribution"],
    "distribution": ["normal_distribution"],
    "regression": ["regression_example", "residual_plot"],
    "correlation": ["correlation_matrix", "scatter_correlation"],
    "hypothesis": ["hypothesis_test"],
    "t-test": ["hypothesis_test", "t_distribution"],
    "confidence": ["confidence_interval"],
    "anova": ["anova_boxplot"],
    "sampling": ["sampling_distribution"],
    "binomial": ["binomial_distribution"],
    "poisson": ["poisson_distribution"],
}

FALLBACK_QUERY = "key concepts statistics regression correlation hypothesis"

CONCEPTS_FILE = None  # Set to Path("stats_concepts.md") if you have one

API_TOPICS = [
    {"id": "probability", "name": "Probability & Distributions", "icon": "🎲"},
    {"id": "sampling", "name": "Sampling Theory", "icon": "📊"},
    {"id": "hypothesis", "name": "Hypothesis Testing", "icon": "🔬"},
    {"id": "correlation", "name": "Correlation", "icon": "📈"},
    {"id": "linear_regression", "name": "Linear Regression", "icon": "📉"},
    {"id": "multiple_regression", "name": "Multiple Regression", "icon": "🔢"},
    {"id": "assumptions", "name": "Regression Assumptions", "icon": "✅"},
    {"id": "interactions", "name": "Interactions", "icon": "🔀"},
    {"id": "categorical", "name": "Categorical Variables", "icon": "🏷️"},
    {"id": "mixed_models", "name": "Mixed Models", "icon": "🔄"},
    {"id": "growth_curves", "name": "Growth Curve Modeling", "icon": "📈"},
]
