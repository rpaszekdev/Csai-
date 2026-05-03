#!/usr/bin/env python3
"""
Graph Manager - Image extraction from PDFs and statistical graph generation.
Provides visualizations for study sessions.

Enhanced with RAG integration:
- First searches lecture PDFs for relevant existing graphs/figures
- Uses Haiku vision model to filter images by relevance to topic
- Falls back to generating statistical visualizations if none found
"""

import hashlib
import json
import logging
import subprocess
import base64
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import re

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Tkinter compatibility
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tempfile

logger = logging.getLogger(__name__)

# Try to import RAG functions for intelligent image retrieval
try:
    from study_rag import retrieve_images_for_topic, retrieve_context
    HAS_RAG = True
except ImportError:
    HAS_RAG = False
    logger.info("RAG system not available for image retrieval")

# Storage directory for images
IMAGES_DIR = Path(__file__).parent / "saved_content" / "images"


@dataclass
class ImageInfo:
    """Information about an extracted or generated image."""
    path: str
    source: str  # 'extracted' or 'generated'
    topic: str
    description: str = ""
    page: Optional[int] = None
    graph_type: Optional[str] = None
    pdf_source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageInfo':
        return cls(**data)


class GraphGenerator:
    """Generates visualizations for study topics."""

    # Topic keywords to graph type mapping - loaded from subject config
    try:
        import subject_config as _sc
        TOPIC_GRAPH_MAP = _sc.TOPIC_GRAPH_MAP
    except ImportError:
        TOPIC_GRAPH_MAP = {}

    def __init__(self, output_dir: Path, colors: Optional[Dict] = None):
        self.output_dir = output_dir
        # Merge passed colors with defaults to ensure all keys exist
        self.colors = self._default_colors()
        if colors:
            self.colors.update(colors)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _default_colors(self) -> Dict[str, str]:
        """Default color scheme matching dark theme."""
        return {
            "primary": "#7c3aed",
            "secondary": "#22d3ee",
            "success": "#22c55e",
            "warning": "#eab308",
            "danger": "#ef4444",
            "bg": "#1a1a24",
            "surface": "#1e2029",
            "text": "#f8fafc",
            "text_muted": "#71717a",
            "text_secondary": "#a1a1aa",
            "grid": "#2a2a3a",
            "border": "#3d4052",
            "content_bg": "#1a1a24",
        }

    def _setup_style(self, fig, ax):
        """Apply consistent styling to figure and axes."""
        fig.patch.set_facecolor(self.colors["bg"])
        ax.set_facecolor(self.colors["bg"])
        ax.tick_params(colors=self.colors["text"], which='both')
        ax.spines['bottom'].set_color(self.colors["grid"])
        ax.spines['top'].set_color(self.colors["grid"])
        ax.spines['left'].set_color(self.colors["grid"])
        ax.spines['right'].set_color(self.colors["grid"])
        ax.xaxis.label.set_color(self.colors["text"])
        ax.yaxis.label.set_color(self.colors["text"])
        ax.title.set_color(self.colors["text"])
        ax.grid(True, alpha=0.2, color=self.colors["grid"])

    def generate_for_topic(self, topic: str) -> List[ImageInfo]:
        """Generate appropriate graphs based on topic keywords."""
        topic_lower = topic.lower()
        graphs_to_generate = set()

        for keyword, graph_types in self.TOPIC_GRAPH_MAP.items():
            if keyword in topic_lower:
                graphs_to_generate.update(graph_types)

        # Default to normal distribution if no specific match
        if not graphs_to_generate:
            graphs_to_generate.add("normal_distribution")

        results = []
        for graph_type in graphs_to_generate:
            method = getattr(self, graph_type, None)
            if method:
                try:
                    image_info = method(topic)
                    if image_info:
                        results.append(image_info)
                except Exception as e:
                    logger.error(f"Error generating {graph_type}: {e}")

        return results

    def normal_distribution(self, topic: str) -> ImageInfo:
        """Generate normal distribution visualization."""
        fig, ax = plt.subplots(figsize=(9, 6))
        self._setup_style(fig, ax)

        x = np.linspace(-4, 4, 1000)
        y = (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * x**2)

        # Main curve
        ax.plot(x, y, color=self.colors["primary"], linewidth=2.5, label='N(0,1)')
        ax.fill_between(x, y, alpha=0.3, color=self.colors["primary"])

        # Standard deviation regions
        colors_sd = [self.colors["success"], self.colors["warning"], self.colors["danger"]]
        labels = ['68% (±1σ)', '95% (±2σ)', '99.7% (±3σ)']

        for i, (sd, color, label) in enumerate(zip([1, 2, 3], colors_sd, labels)):
            ax.axvline(x=-sd, color=color, linestyle='--', alpha=0.7, linewidth=1.5)
            ax.axvline(x=sd, color=color, linestyle='--', alpha=0.7, linewidth=1.5)

        # Add annotations
        ax.annotate('μ', xy=(0, 0.42), fontsize=14, color=self.colors["text"],
                   ha='center', fontweight='bold')
        ax.annotate('68%', xy=(0, 0.15), fontsize=11, color=self.colors["success"],
                   ha='center', alpha=0.9)

        ax.set_xlabel("Standard Deviations (σ)", fontsize=12)
        ax.set_ylabel("Probability Density", fontsize=12)
        ax.set_title("Standard Normal Distribution", fontsize=16, fontweight='bold', pad=15)
        ax.set_xlim(-4, 4)
        ax.set_ylim(0, 0.45)

        output_path = self.output_dir / "normal_distribution.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Standard Normal Distribution showing probability density and standard deviation regions",
            graph_type="normal_distribution"
        )

    def regression_example(self, topic: str) -> ImageInfo:
        """Generate linear regression visualization."""
        fig, ax = plt.subplots(figsize=(9, 6))
        self._setup_style(fig, ax)

        np.random.seed(42)
        x = np.linspace(1, 10, 40)
        y = 2.5 * x + 3 + np.random.normal(0, 2.5, 40)

        # Scatter plot
        ax.scatter(x, y, color=self.colors["secondary"], alpha=0.7, s=60,
                  edgecolors='white', linewidth=0.5, label='Data points')

        # Regression line
        coeffs = np.polyfit(x, y, 1)
        y_pred = np.polyval(coeffs, x)
        ax.plot(x, y_pred, color=self.colors["primary"], linewidth=2.5,
               label=f'ŷ = {coeffs[0]:.2f}x + {coeffs[1]:.2f}')

        # Confidence band (simplified)
        residuals = y - y_pred
        std_err = np.std(residuals)
        ax.fill_between(x, y_pred - 1.96*std_err, y_pred + 1.96*std_err,
                       alpha=0.2, color=self.colors["primary"], label='95% CI')

        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10)
        ax.set_xlabel("X (Independent Variable)", fontsize=12)
        ax.set_ylabel("Y (Dependent Variable)", fontsize=12)
        ax.set_title("Linear Regression", fontsize=16, fontweight='bold', pad=15)

        output_path = self.output_dir / "regression_example.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Linear regression showing fitted line with 95% confidence interval",
            graph_type="regression_example"
        )

    def residual_plot(self, topic: str) -> ImageInfo:
        """Generate residual plot for regression diagnostics."""
        fig, ax = plt.subplots(figsize=(9, 6))
        self._setup_style(fig, ax)

        np.random.seed(42)
        x = np.linspace(1, 10, 40)
        y = 2.5 * x + 3 + np.random.normal(0, 2.5, 40)
        coeffs = np.polyfit(x, y, 1)
        y_pred = np.polyval(coeffs, x)
        residuals = y - y_pred

        ax.scatter(y_pred, residuals, color=self.colors["secondary"], alpha=0.7, s=60,
                  edgecolors='white', linewidth=0.5)
        ax.axhline(y=0, color=self.colors["danger"], linestyle='--', linewidth=2, alpha=0.8)

        # Add reference bands
        std_resid = np.std(residuals)
        ax.axhline(y=2*std_resid, color=self.colors["warning"], linestyle=':', alpha=0.5)
        ax.axhline(y=-2*std_resid, color=self.colors["warning"], linestyle=':', alpha=0.5)

        ax.set_xlabel("Fitted Values (ŷ)", fontsize=12)
        ax.set_ylabel("Residuals (y - ŷ)", fontsize=12)
        ax.set_title("Residual Plot", fontsize=16, fontweight='bold', pad=15)

        output_path = self.output_dir / "residual_plot.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Residual plot for checking regression assumptions (homoscedasticity)",
            graph_type="residual_plot"
        )

    def correlation_matrix(self, topic: str) -> ImageInfo:
        """Generate correlation matrix heatmap."""
        fig, ax = plt.subplots(figsize=(8, 7))
        self._setup_style(fig, ax)

        np.random.seed(42)
        # Create correlated data
        data = np.random.randn(100, 5)
        data[:, 1] = data[:, 0] * 0.8 + np.random.randn(100) * 0.5
        data[:, 2] = data[:, 0] * -0.6 + np.random.randn(100) * 0.7
        data[:, 3] = np.random.randn(100)
        data[:, 4] = data[:, 1] * 0.5 + np.random.randn(100) * 0.8

        corr = np.corrcoef(data.T)
        labels = ['Var A', 'Var B', 'Var C', 'Var D', 'Var E']

        # Custom colormap
        cmap = sns.diverging_palette(250, 15, s=75, l=40, n=9, center='dark', as_cmap=True)

        im = ax.imshow(corr, cmap=cmap, vmin=-1, vmax=1, aspect='auto')

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.ax.tick_params(colors=self.colors["text"])
        cbar.outline.set_edgecolor(self.colors["grid"])

        # Add correlation values
        for i in range(len(labels)):
            for j in range(len(labels)):
                text_color = 'white' if abs(corr[i, j]) > 0.5 else self.colors["text"]
                ax.text(j, i, f'{corr[i, j]:.2f}', ha='center', va='center',
                       color=text_color, fontsize=11, fontweight='bold')

        ax.set_xticks(range(len(labels)))
        ax.set_yticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=11)
        ax.set_yticklabels(labels, fontsize=11)
        ax.set_title("Correlation Matrix", fontsize=16, fontweight='bold', pad=15)

        output_path = self.output_dir / "correlation_matrix.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Correlation matrix heatmap showing relationships between variables",
            graph_type="correlation_matrix"
        )

    def hypothesis_test(self, topic: str) -> ImageInfo:
        """Generate hypothesis test visualization with p-value regions."""
        fig, ax = plt.subplots(figsize=(10, 6))
        self._setup_style(fig, ax)

        x = np.linspace(-4, 4, 1000)
        y = (1 / np.sqrt(2 * np.pi)) * np.exp(-0.5 * x**2)

        # Main distribution
        ax.plot(x, y, color=self.colors["text"], linewidth=2, label='Null Distribution')
        ax.fill_between(x, y, alpha=0.1, color=self.colors["text"])

        # Critical regions (α = 0.05, two-tailed)
        critical = 1.96
        ax.fill_between(x[x <= -critical], y[x <= -critical],
                       color=self.colors["danger"], alpha=0.6, label='Rejection Region (α/2)')
        ax.fill_between(x[x >= critical], y[x >= critical],
                       color=self.colors["danger"], alpha=0.6)

        # Test statistic example
        test_stat = 2.3
        ax.axvline(x=test_stat, color=self.colors["warning"], linewidth=2.5,
                  linestyle='-', label=f'Test Statistic = {test_stat}')
        ax.plot(test_stat, 0.02, marker='v', markersize=12, color=self.colors["warning"])

        # Annotations
        ax.annotate('α/2 = 0.025', xy=(-2.5, 0.03), fontsize=10,
                   color=self.colors["danger"], fontweight='bold')
        ax.annotate('α/2 = 0.025', xy=(2.1, 0.03), fontsize=10,
                   color=self.colors["danger"], fontweight='bold')
        ax.annotate('Fail to Reject H₀\n(Accept Region)', xy=(0, 0.2), fontsize=11,
                   color=self.colors["success"], ha='center', fontweight='bold')

        ax.axvline(x=-critical, color=self.colors["danger"], linestyle='--', alpha=0.7)
        ax.axvline(x=critical, color=self.colors["danger"], linestyle='--', alpha=0.7)

        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10, loc='upper right')
        ax.set_xlabel("Test Statistic (z)", fontsize=12)
        ax.set_ylabel("Probability Density", fontsize=12)
        ax.set_title("Two-Tailed Hypothesis Test (α = 0.05)", fontsize=16, fontweight='bold', pad=15)
        ax.set_xlim(-4, 4)
        ax.set_ylim(0, 0.45)

        output_path = self.output_dir / "hypothesis_test.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Hypothesis test visualization showing rejection regions and test statistic",
            graph_type="hypothesis_test"
        )

    def confidence_interval(self, topic: str) -> ImageInfo:
        """Generate confidence interval visualization."""
        fig, ax = plt.subplots(figsize=(10, 6))
        self._setup_style(fig, ax)

        np.random.seed(42)
        n_samples = 20
        true_mean = 50
        sample_means = []
        sample_cis = []

        for i in range(n_samples):
            sample = np.random.normal(true_mean, 10, 30)
            mean = np.mean(sample)
            se = np.std(sample, ddof=1) / np.sqrt(30)
            ci = 1.96 * se
            sample_means.append(mean)
            sample_cis.append(ci)

        # Plot confidence intervals
        colors_ci = []
        for i, (mean, ci) in enumerate(zip(sample_means, sample_cis)):
            contains_true = (mean - ci <= true_mean <= mean + ci)
            color = self.colors["success"] if contains_true else self.colors["danger"]
            colors_ci.append(color)
            ax.errorbar(mean, i, xerr=ci, fmt='o', color=color,
                       capsize=4, capthick=1.5, markersize=6, linewidth=1.5)

        # True population mean
        ax.axvline(x=true_mean, color=self.colors["primary"], linewidth=2.5,
                  linestyle='-', label=f'True μ = {true_mean}')

        # Count CIs containing true mean
        n_contain = sum(1 for m, ci in zip(sample_means, sample_cis)
                       if m - ci <= true_mean <= m + ci)

        ax.text(0.02, 0.98, f'{n_contain}/{n_samples} CIs contain true μ',
               transform=ax.transAxes, fontsize=11, verticalalignment='top',
               color=self.colors["text"], fontweight='bold',
               bbox=dict(boxstyle='round', facecolor=self.colors["surface"],
                        edgecolor=self.colors["grid"]))

        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10, loc='lower right')
        ax.set_xlabel("Value", fontsize=12)
        ax.set_ylabel("Sample Number", fontsize=12)
        ax.set_title("95% Confidence Intervals from 20 Samples", fontsize=16, fontweight='bold', pad=15)

        output_path = self.output_dir / "confidence_interval.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Multiple 95% confidence intervals showing coverage of true population mean",
            graph_type="confidence_interval"
        )

    def t_distribution(self, topic: str) -> ImageInfo:
        """Generate t-distribution comparison with normal."""
        from scipy import stats

        fig, ax = plt.subplots(figsize=(9, 6))
        self._setup_style(fig, ax)

        x = np.linspace(-4, 4, 1000)

        # Normal distribution
        y_normal = stats.norm.pdf(x)
        ax.plot(x, y_normal, color=self.colors["text"], linewidth=2,
               label='Normal (z)', alpha=0.8)

        # t-distributions with different df
        dfs = [3, 10, 30]
        colors_t = [self.colors["danger"], self.colors["warning"], self.colors["success"]]
        for df, color in zip(dfs, colors_t):
            y_t = stats.t.pdf(x, df)
            ax.plot(x, y_t, color=color, linewidth=2, label=f't (df={df})')

        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10)
        ax.set_xlabel("Value", fontsize=12)
        ax.set_ylabel("Probability Density", fontsize=12)
        ax.set_title("t-Distribution vs Normal Distribution", fontsize=16, fontweight='bold', pad=15)

        output_path = self.output_dir / "t_distribution.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Comparison of t-distributions with different degrees of freedom vs normal",
            graph_type="t_distribution"
        )

    def sampling_distribution(self, topic: str) -> ImageInfo:
        """Generate sampling distribution demonstration (CLT)."""
        fig, axes = plt.subplots(1, 3, figsize=(14, 5))
        fig.patch.set_facecolor(self.colors["bg"])

        np.random.seed(42)

        # Original skewed distribution
        population = np.random.exponential(scale=2, size=10000)

        titles = ['Population\n(Exponential)', 'Sampling Dist.\n(n=5)', 'Sampling Dist.\n(n=30)']
        sample_sizes = [None, 5, 30]

        for i, (ax, title, n) in enumerate(zip(axes, titles, sample_sizes)):
            self._setup_style(fig, ax)

            if n is None:
                data = population
                color = self.colors["secondary"]
            else:
                data = [np.mean(np.random.choice(population, n)) for _ in range(1000)]
                color = self.colors["primary"] if n == 30 else self.colors["warning"]

            ax.hist(data, bins=40, color=color, alpha=0.7, edgecolor='white', linewidth=0.5)
            ax.axvline(np.mean(data), color=self.colors["danger"], linewidth=2,
                      linestyle='--', label=f'Mean = {np.mean(data):.2f}')
            ax.set_title(title, fontsize=13, fontweight='bold', color=self.colors["text"])
            ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                     edgecolor=self.colors["grid"], fontsize=9)

        fig.suptitle("Central Limit Theorem Demonstration", fontsize=16,
                    fontweight='bold', color=self.colors["text"], y=1.02)
        plt.tight_layout()

        output_path = self.output_dir / "sampling_distribution.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Central Limit Theorem: sampling distributions become normal as n increases",
            graph_type="sampling_distribution"
        )

    def anova_boxplot(self, topic: str) -> ImageInfo:
        """Generate ANOVA-style boxplot comparison."""
        fig, ax = plt.subplots(figsize=(9, 6))
        self._setup_style(fig, ax)

        np.random.seed(42)
        groups = {
            'Group A': np.random.normal(20, 3, 30),
            'Group B': np.random.normal(25, 4, 30),
            'Group C': np.random.normal(22, 3.5, 30),
            'Group D': np.random.normal(28, 3, 30),
        }

        positions = range(1, len(groups) + 1)
        bp = ax.boxplot(groups.values(), positions=positions, patch_artist=True,
                       widths=0.6, showfliers=True)

        colors_box = [self.colors["primary"], self.colors["secondary"],
                     self.colors["success"], self.colors["warning"]]

        for patch, color in zip(bp['boxes'], colors_box):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        for element in ['whiskers', 'caps', 'medians']:
            for item in bp[element]:
                item.set_color(self.colors["text"])
                item.set_linewidth(1.5)

        for flier in bp['fliers']:
            flier.set_markerfacecolor(self.colors["danger"])
            flier.set_markeredgecolor(self.colors["danger"])

        ax.set_xticklabels(groups.keys(), fontsize=11)
        ax.set_xlabel("Groups", fontsize=12)
        ax.set_ylabel("Value", fontsize=12)
        ax.set_title("ANOVA: Comparing Group Means", fontsize=16, fontweight='bold', pad=15)

        # Add grand mean line
        all_data = np.concatenate(list(groups.values()))
        ax.axhline(np.mean(all_data), color=self.colors["danger"], linestyle='--',
                  linewidth=1.5, label=f'Grand Mean = {np.mean(all_data):.1f}')
        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10)

        output_path = self.output_dir / "anova_boxplot.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Box plots comparing multiple groups for ANOVA analysis",
            graph_type="anova_boxplot"
        )

    def poisson_distribution(self, topic: str) -> ImageInfo:
        """Generate Poisson distribution visualization."""
        from scipy import stats

        fig, ax = plt.subplots(figsize=(9, 6))
        self._setup_style(fig, ax)

        # Different lambda values
        lambdas = [1, 4, 10]
        colors_p = [self.colors["primary"], self.colors["secondary"], self.colors["success"]]

        for lam, color in zip(lambdas, colors_p):
            x = np.arange(0, 25)
            y = stats.poisson.pmf(x, lam)
            ax.bar(x + lam/15 - 0.2, y, width=0.25, alpha=0.7, color=color,
                   label=f'λ = {lam}', edgecolor='white')

        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10)
        ax.set_xlabel("Number of Events (k)", fontsize=12)
        ax.set_ylabel("Probability P(X = k)", fontsize=12)
        ax.set_title("Poisson Distribution", fontsize=16, fontweight='bold', pad=15)
        ax.set_xlim(-0.5, 20)

        output_path = self.output_dir / "poisson_distribution.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Poisson distribution showing probability mass function for different λ values",
            graph_type="poisson_distribution"
        )

    def binomial_distribution(self, topic: str) -> ImageInfo:
        """Generate Binomial distribution visualization."""
        from scipy import stats

        fig, ax = plt.subplots(figsize=(9, 6))
        self._setup_style(fig, ax)

        n = 20  # number of trials
        probs = [0.2, 0.5, 0.8]
        colors_b = [self.colors["primary"], self.colors["secondary"], self.colors["success"]]

        for p, color in zip(probs, colors_b):
            x = np.arange(0, n + 1)
            y = stats.binom.pmf(x, n, p)
            ax.bar(x + p/5 - 0.2, y, width=0.2, alpha=0.7, color=color,
                   label=f'p = {p}', edgecolor='white')

        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10)
        ax.set_xlabel("Number of Successes (k)", fontsize=12)
        ax.set_ylabel("Probability P(X = k)", fontsize=12)
        ax.set_title(f"Binomial Distribution (n = {n})", fontsize=16, fontweight='bold', pad=15)

        output_path = self.output_dir / "binomial_distribution.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Binomial distribution showing PMF for different probability values",
            graph_type="binomial_distribution"
        )

    def chi_square_distribution(self, topic: str) -> ImageInfo:
        """Generate Chi-square distribution visualization."""
        from scipy import stats

        fig, ax = plt.subplots(figsize=(9, 6))
        self._setup_style(fig, ax)

        x = np.linspace(0, 20, 500)
        dfs = [2, 4, 6, 9]
        colors_chi = [self.colors["danger"], self.colors["warning"],
                      self.colors["primary"], self.colors["success"]]

        for df, color in zip(dfs, colors_chi):
            y = stats.chi2.pdf(x, df)
            ax.plot(x, y, color=color, linewidth=2, label=f'df = {df}')
            ax.fill_between(x, y, alpha=0.1, color=color)

        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10)
        ax.set_xlabel("χ² Value", fontsize=12)
        ax.set_ylabel("Probability Density", fontsize=12)
        ax.set_title("Chi-Square (χ²) Distribution", fontsize=16, fontweight='bold', pad=15)
        ax.set_xlim(0, 20)
        ax.set_ylim(0, 0.5)

        output_path = self.output_dir / "chi_square_distribution.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Chi-square distribution with different degrees of freedom",
            graph_type="chi_square_distribution"
        )

    def model_comparison(self, topic: str) -> ImageInfo:
        """Generate AIC/BIC model comparison visualization."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.patch.set_facecolor(self.colors["bg"])

        np.random.seed(42)

        # Left plot: AIC/BIC bar comparison across models
        ax = axes[0]
        self._setup_style(fig, ax)

        models = ['Model 1\n(Intercept)', 'Model 2\n(+X1)', 'Model 3\n(+X1,X2)',
                  'Model 4\n(+X1,X2,X3)', 'Model 5\n(Full)']

        # Simulate realistic AIC/BIC values (lower is better)
        # Model 3 is "best" - not too simple, not overfit
        aic_values = [450, 380, 320, 325, 340]
        bic_values = [455, 390, 340, 360, 390]

        x = np.arange(len(models))
        width = 0.35

        bars1 = ax.bar(x - width/2, aic_values, width, label='AIC',
                       color=self.colors["primary"], alpha=0.8, edgecolor='white')
        bars2 = ax.bar(x + width/2, bic_values, width, label='BIC',
                       color=self.colors["secondary"], alpha=0.8, edgecolor='white')

        # Highlight the best model
        best_idx = 2  # Model 3 has lowest AIC
        ax.axhline(y=aic_values[best_idx], color=self.colors["success"],
                   linestyle='--', alpha=0.7, linewidth=1.5)

        # Add star to best model
        ax.annotate('★ Best', xy=(best_idx, aic_values[best_idx] - 15),
                   fontsize=11, color=self.colors["success"], ha='center', fontweight='bold')

        ax.set_xlabel('Models', fontsize=12)
        ax.set_ylabel('Information Criterion Value', fontsize=12)
        ax.set_title('AIC vs BIC: Model Selection\n(Lower = Better)', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(models, fontsize=9)
        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10)
        ax.set_ylim(250, 500)

        # Right plot: Log-Likelihood vs complexity trade-off
        ax = axes[1]
        self._setup_style(fig, ax)

        # Number of parameters (complexity)
        n_params = [1, 2, 3, 4, 5]
        log_lik = [-220, -185, -155, -152, -150]  # Increases (gets better) with complexity

        # Plot log-likelihood curve
        ax.plot(n_params, log_lik, 'o-', color=self.colors["primary"],
                linewidth=2, markersize=10, label='Log-Likelihood')

        # Add AIC penalty visualization
        aic_penalty = [2*k for k in n_params]  # AIC penalty = 2k
        adjusted = [ll - pen/10 for ll, pen in zip(log_lik, aic_penalty)]  # Scaled for visualization
        ax.plot(n_params, adjusted, 's--', color=self.colors["warning"],
                linewidth=2, markersize=8, alpha=0.8, label='Adjusted (with penalty)')

        # Highlight diminishing returns
        ax.annotate('Diminishing\nreturns', xy=(4.5, -151), fontsize=10,
                   color=self.colors["text_muted"], ha='center')
        ax.annotate('', xy=(5, -150), xytext=(3.5, -156),
                   arrowprops=dict(arrowstyle='->', color=self.colors["text_muted"], alpha=0.5))

        ax.set_xlabel('Number of Parameters (k)', fontsize=12)
        ax.set_ylabel('Log-Likelihood', fontsize=12)
        ax.set_title('Log-Likelihood vs Model Complexity\n(Higher LL = Better Fit)', fontsize=14, fontweight='bold')
        ax.legend(facecolor=self.colors["surface"], labelcolor=self.colors["text"],
                 edgecolor=self.colors["grid"], fontsize=10, loc='lower right')

        # Add formula annotations
        fig.text(0.25, 0.02, 'AIC = -2·ln(L) + 2k', fontsize=10,
                color=self.colors["text_muted"], ha='center', style='italic')
        fig.text(0.75, 0.02, 'BIC = -2·ln(L) + k·ln(n)', fontsize=10,
                color=self.colors["text_muted"], ha='center', style='italic')

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.12)

        output_path = self.output_dir / "model_comparison.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="AIC/BIC model comparison and log-likelihood trade-off visualization",
            graph_type="model_comparison"
        )

    def assumption_residual_comparison(self, topic: str) -> ImageInfo:
        """Generate residual plots showing GOOD vs VIOLATED assumptions."""
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.patch.set_facecolor(self.colors["bg"])

        np.random.seed(42)
        n = 50

        # Top-left: GOOD - Homoscedasticity (constant variance)
        ax = axes[0, 0]
        self._setup_style(fig, ax)
        x = np.linspace(1, 10, n)
        residuals_good = np.random.normal(0, 1.5, n)
        ax.scatter(x, residuals_good, color=self.colors["success"], alpha=0.7, s=50)
        ax.axhline(0, color='white', linestyle='--', alpha=0.5)
        ax.set_title("✓ GOOD: Constant Variance", fontsize=12, color=self.colors["success"])
        ax.set_xlabel("Fitted Values")
        ax.set_ylabel("Residuals")

        # Top-right: BAD - Heteroscedasticity (increasing variance)
        ax = axes[0, 1]
        self._setup_style(fig, ax)
        residuals_hetero = np.random.normal(0, 1, n) * (x / 2)
        ax.scatter(x, residuals_hetero, color=self.colors["danger"], alpha=0.7, s=50)
        ax.axhline(0, color='white', linestyle='--', alpha=0.5)
        ax.set_title("✗ VIOLATED: Heteroscedasticity", fontsize=12, color=self.colors["danger"])
        ax.set_xlabel("Fitted Values")
        ax.set_ylabel("Residuals")

        # Bottom-left: GOOD - Linear relationship (random residuals)
        ax = axes[1, 0]
        self._setup_style(fig, ax)
        ax.scatter(x, residuals_good, color=self.colors["success"], alpha=0.7, s=50)
        ax.axhline(0, color='white', linestyle='--', alpha=0.5)
        ax.set_title("✓ GOOD: Linear Relationship", fontsize=12, color=self.colors["success"])
        ax.set_xlabel("Fitted Values")
        ax.set_ylabel("Residuals")

        # Bottom-right: BAD - Non-linear pattern (curved residuals)
        ax = axes[1, 1]
        self._setup_style(fig, ax)
        residuals_curved = np.sin(x) * 3 + np.random.normal(0, 0.5, n)
        ax.scatter(x, residuals_curved, color=self.colors["danger"], alpha=0.7, s=50)
        ax.axhline(0, color='white', linestyle='--', alpha=0.5)
        ax.set_title("✗ VIOLATED: Non-linear Pattern", fontsize=12, color=self.colors["danger"])
        ax.set_xlabel("Fitted Values")
        ax.set_ylabel("Residuals")

        fig.suptitle("Residual Plots: Checking Regression Assumptions",
                    fontsize=14, fontweight='bold', color=self.colors["text"], y=0.98)
        plt.tight_layout()

        output_path = self.output_dir / "assumption_residuals.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Residual plots comparing good vs violated regression assumptions",
            graph_type="assumption_residual_comparison"
        )

    def assumption_normality_comparison(self, topic: str) -> ImageInfo:
        """Generate Q-Q plots and histograms showing GOOD vs VIOLATED normality."""
        from scipy import stats

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.patch.set_facecolor(self.colors["bg"])

        np.random.seed(42)
        n = 100

        # Generate data
        normal_data = np.random.normal(0, 1, n)
        skewed_data = np.random.exponential(1, n) - 1  # Right-skewed

        # Top-left: GOOD - Normal histogram
        ax = axes[0, 0]
        self._setup_style(fig, ax)
        ax.hist(normal_data, bins=20, color=self.colors["success"], alpha=0.7, edgecolor='white')
        ax.set_title("✓ GOOD: Normal Distribution", fontsize=12, color=self.colors["success"])
        ax.set_xlabel("Residuals")
        ax.set_ylabel("Frequency")

        # Top-right: BAD - Skewed histogram
        ax = axes[0, 1]
        self._setup_style(fig, ax)
        ax.hist(skewed_data, bins=20, color=self.colors["danger"], alpha=0.7, edgecolor='white')
        ax.set_title("✗ VIOLATED: Right-Skewed", fontsize=12, color=self.colors["danger"])
        ax.set_xlabel("Residuals")
        ax.set_ylabel("Frequency")

        # Bottom-left: GOOD - Q-Q plot (normal)
        ax = axes[1, 0]
        self._setup_style(fig, ax)
        stats.probplot(normal_data, dist="norm", plot=ax)
        ax.get_lines()[0].set_color(self.colors["success"])
        ax.get_lines()[0].set_markersize(5)
        ax.get_lines()[1].set_color('white')
        ax.set_title("✓ GOOD: Q-Q Plot (Points on Line)", fontsize=12, color=self.colors["success"])

        # Bottom-right: BAD - Q-Q plot (skewed)
        ax = axes[1, 1]
        self._setup_style(fig, ax)
        stats.probplot(skewed_data, dist="norm", plot=ax)
        ax.get_lines()[0].set_color(self.colors["danger"])
        ax.get_lines()[0].set_markersize(5)
        ax.get_lines()[1].set_color('white')
        ax.set_title("✗ VIOLATED: Q-Q Plot (Curved Pattern)", fontsize=12, color=self.colors["danger"])

        fig.suptitle("Normality Check: Histogram & Q-Q Plot Comparison",
                    fontsize=14, fontweight='bold', color=self.colors["text"], y=0.98)
        plt.tight_layout()

        output_path = self.output_dir / "assumption_normality.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Normality assumption: histogram and Q-Q plot comparison (good vs violated)",
            graph_type="assumption_normality_comparison"
        )

    def assumption_independence_comparison(self, topic: str) -> ImageInfo:
        """Generate plots showing GOOD vs VIOLATED independence assumption."""
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.patch.set_facecolor(self.colors["bg"])

        np.random.seed(42)
        n = 50

        # Left: GOOD - Independent residuals (random pattern)
        ax = axes[0]
        self._setup_style(fig, ax)
        residuals_indep = np.random.normal(0, 1, n)
        ax.plot(range(n), residuals_indep, 'o-', color=self.colors["success"], alpha=0.7, markersize=5)
        ax.axhline(0, color='white', linestyle='--', alpha=0.5)
        ax.set_title("✓ GOOD: Independent (Random Pattern)", fontsize=12, color=self.colors["success"])
        ax.set_xlabel("Observation Order")
        ax.set_ylabel("Residuals")

        # Right: BAD - Autocorrelated residuals (pattern)
        ax = axes[1]
        self._setup_style(fig, ax)
        autocorr = np.zeros(n)
        autocorr[0] = np.random.normal(0, 1)
        for i in range(1, n):
            autocorr[i] = 0.8 * autocorr[i-1] + np.random.normal(0, 0.5)
        ax.plot(range(n), autocorr, 'o-', color=self.colors["danger"], alpha=0.7, markersize=5)
        ax.axhline(0, color='white', linestyle='--', alpha=0.5)
        ax.set_title("✗ VIOLATED: Autocorrelation (Runs Pattern)", fontsize=12, color=self.colors["danger"])
        ax.set_xlabel("Observation Order")
        ax.set_ylabel("Residuals")

        fig.suptitle("Independence Assumption: Residuals vs Order",
                    fontsize=14, fontweight='bold', color=self.colors["text"], y=1.02)
        plt.tight_layout()

        output_path = self.output_dir / "assumption_independence.png"
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=self.colors["bg"])
        plt.close(fig)

        return ImageInfo(
            path=str(output_path),
            source="generated",
            topic=topic,
            description="Independence assumption: random vs autocorrelated residuals",
            graph_type="assumption_independence_comparison"
        )


class GraphManager:
    """Manages image extraction from PDFs and graph generation for study topics."""

    def __init__(self, storage_dir: Optional[Path] = None, colors: Optional[Dict] = None):
        self.storage_dir = storage_dir or IMAGES_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.colors = colors
        self.generator = GraphGenerator(self.storage_dir, colors)
        self.metadata_file = self.storage_dir / "image_metadata.json"

    def _load_metadata(self) -> Dict[str, List[Dict]]:
        """Load image metadata from JSON file."""
        if self.metadata_file.exists():
            try:
                return json.loads(self.metadata_file.read_text())
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def _save_metadata(self, metadata: Dict[str, List[Dict]]):
        """Save image metadata to JSON file."""
        self.metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    def _get_topic_hash(self, topic: str) -> str:
        """Generate a short hash for topic to use as directory name."""
        return hashlib.md5(topic.lower().encode()).hexdigest()[:12]

    def extract_images_from_pdf(self, pdf_path: Path, topic: str,
                                 pages: Optional[List[int]] = None) -> List[ImageInfo]:
        """
        Extract images from a PDF file.

        Args:
            pdf_path: Path to the PDF file
            topic: Topic to associate images with
            pages: Optional list of page numbers to extract from (1-indexed)

        Returns:
            List of ImageInfo objects for extracted images
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.warning("PyMuPDF not installed. Cannot extract images from PDFs.")
            return []

        extracted = []
        topic_hash = self._get_topic_hash(topic)
        topic_dir = self.storage_dir / topic_hash
        topic_dir.mkdir(parents=True, exist_ok=True)

        try:
            doc = fitz.open(str(pdf_path))

            for page_num in range(len(doc)):
                # Skip if specific pages requested and this isn't one
                if pages and (page_num + 1) not in pages:
                    continue

                page = doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # Filter small images (likely icons/bullets/decorations)
                        # Require at least 300x200 for meaningful figures (graphs, charts)
                        if base_image["width"] < 300 or base_image["height"] < 200:
                            continue

                        # Also skip very narrow or very wide images (likely banners/lines)
                        aspect_ratio = base_image["width"] / base_image["height"]
                        if aspect_ratio > 4 or aspect_ratio < 0.25:
                            continue

                        # Save image
                        image_filename = f"extracted_p{page_num + 1}_{img_index}.{image_ext}"
                        image_path = topic_dir / image_filename

                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)

                        # Create descriptive text including topic context
                        lecture_name = pdf_path.stem.replace("_", " ").replace("-", " ")
                        description = f"Lecture figure for '{topic}' - from {lecture_name}, page {page_num + 1}"

                        extracted.append(ImageInfo(
                            path=str(image_path),
                            source="extracted",
                            topic=topic,
                            description=description,
                            page=page_num + 1,
                            pdf_source=str(pdf_path)
                        ))

                    except Exception as e:
                        logger.debug(f"Could not extract image {img_index} from page {page_num}: {e}")

            doc.close()

        except Exception as e:
            logger.error(f"Error extracting images from PDF {pdf_path}: {e}")

        return extracted

    def _create_numbered_grid_image(self, images: List[ImageInfo],
                                     max_cols: int = 4,
                                     cell_size: int = 300) -> Optional[str]:
        """
        Create a single grid image with all extracted images numbered.

        Args:
            images: List of ImageInfo objects to combine
            max_cols: Maximum columns in the grid
            cell_size: Size of each cell in pixels

        Returns:
            Path to the temporary grid image, or None if failed
        """
        if not images:
            return None

        valid_images = []
        for img in images:
            path = Path(img.path)
            if path.exists():
                try:
                    pil_img = Image.open(path)
                    valid_images.append((img, pil_img))
                except Exception as e:
                    logger.debug(f"Could not open image {path}: {e}")

        if not valid_images:
            return None

        # Calculate grid dimensions
        num_images = len(valid_images)
        cols = min(num_images, max_cols)
        rows = (num_images + cols - 1) // cols

        # Create grid canvas with padding for numbers
        padding = 30  # Space for number labels
        grid_width = cols * cell_size
        grid_height = rows * (cell_size + padding)

        grid = Image.new('RGB', (grid_width, grid_height), color='white')
        draw = ImageDraw.Draw(grid)

        # Try to get a reasonable font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()

        # Place images in grid
        for idx, (img_info, pil_img) in enumerate(valid_images):
            row = idx // cols
            col = idx % cols

            # Resize image to fit cell while maintaining aspect ratio
            pil_img.thumbnail((cell_size - 10, cell_size - 10), Image.Resampling.LANCZOS)

            # Calculate position (centered in cell)
            x = col * cell_size + (cell_size - pil_img.width) // 2
            y = row * (cell_size + padding) + padding + (cell_size - pil_img.height) // 2

            # Draw number label above image
            label = f"[{idx + 1}]"
            label_x = col * cell_size + 5
            label_y = row * (cell_size + padding) + 5
            draw.text((label_x, label_y), label, fill='black', font=font)

            # Paste image
            if pil_img.mode == 'RGBA':
                grid.paste(pil_img, (x, y), pil_img)
            else:
                grid.paste(pil_img, (x, y))

            # Close the individual image
            pil_img.close()

        # Save to project directory (CLI needs access to this location)
        grid_path = self.storage_dir / "_temp_grid.png"
        grid.save(str(grid_path), 'PNG')
        grid.close()

        logger.info(f"Created grid image with {num_images} images: {grid_path}")
        return str(grid_path)

    def _filter_via_cli(self, grid_image_path: str, topic: str,
                        num_images: int) -> List[int]:
        """
        Use Claude CLI with Haiku to determine which images are relevant.

        Args:
            grid_image_path: Path to the combined grid image
            topic: Study topic to filter against
            num_images: Total number of images in the grid

        Returns:
            List of 1-indexed image numbers that are relevant
        """
        # Construct prompt with image path at the start (CLI reads it as image)
        prompt = f'''{grid_image_path}

Look at this numbered grid of images extracted from lecture PDFs.
Which images are relevant to studying "{topic}"?

RELEVANT images show:
- Graphs, charts, or visualizations about {topic}
- Formulas or equations related to {topic}
- R code output or statistical results for {topic}
- Diagrams that explain {topic} concepts

NOT RELEVANT images are:
- University logos, banners, headers
- Content about different statistical topics
- Decorative elements, icons
- Too small or unclear images

Respond with ONLY a JSON object listing the relevant image numbers:
{{"relevant": [1, 3, 5]}}

If none are relevant: {{"relevant": []}}'''

        try:
            result = subprocess.run(
                ['claude', '-p', prompt, '--model', 'opus'],
                capture_output=True,
                text=True,
                timeout=120
            )

            response = result.stdout.strip()
            logger.debug(f"CLI response: {response}")

            # Parse JSON from response
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())
                relevant = data.get("relevant", [])
                # Validate indices
                return [i for i in relevant if 1 <= i <= num_images]
            else:
                logger.warning(f"Could not parse CLI response: {response[:200]}")
                # If parsing fails, keep all images
                return list(range(1, num_images + 1))

        except subprocess.TimeoutExpired:
            logger.error("CLI call timed out")
            return list(range(1, num_images + 1))
        except FileNotFoundError:
            logger.error("Claude CLI not found - ensure 'claude' is in PATH")
            return list(range(1, num_images + 1))
        except Exception as e:
            logger.error(f"Error calling CLI: {e}")
            return list(range(1, num_images + 1))

    def _get_required_graphs_for_topic(self, topic: str) -> List[str]:
        """
        Ask Sonnet what graphs/visualizations are needed to understand a topic.

        Args:
            topic: The study topic

        Returns:
            List of graph descriptions needed (e.g. ["residual plot", "Q-Q plot"])
        """
        import subject_config
        prompt = f'''What graphs or visualizations are essential for understanding "{topic}" in {subject_config.SUBJECT_NAME}?

List 3-6 specific graph types that a student MUST see to properly understand this topic.
Be specific (e.g. "residual vs fitted plot" not just "plot").

Respond with ONLY a JSON object:
{{"required_graphs": ["graph 1", "graph 2", "graph 3"]}}'''

        try:
            result = subprocess.run(
                ['claude', '-p', prompt, '--model', 'opus'],
                capture_output=True,
                text=True,
                timeout=60
            )

            response = result.stdout.strip()
            logger.debug(f"Required graphs response: {response}")

            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())
                graphs = data.get("required_graphs", [])
                logger.info(f"Required graphs for '{topic}': {graphs}")
                return graphs

        except Exception as e:
            logger.error(f"Error getting required graphs: {e}")

        # Fallback to keyword-based mapping
        return self._get_graphs_from_keywords(topic)

    def _get_graphs_from_keywords(self, topic: str) -> List[str]:
        """Fallback: get graph types based on topic keywords."""
        topic_lower = topic.lower()
        graphs = []

        keyword_map = {
            "regression": ["scatter plot with regression line", "residual plot", "Q-Q plot"],
            "assumption": ["residual vs fitted plot", "Q-Q plot", "scale-location plot"],
            "anova": ["boxplot by group", "residual plot", "group means plot"],
            "correlation": ["scatter plot matrix", "correlation heatmap"],
            "distribution": ["histogram", "density plot", "Q-Q plot"],
            "hypothesis": ["t-distribution", "rejection region plot"],
            "confidence": ["confidence interval plot", "error bar plot"],
            "aic": ["AIC/BIC comparison bar chart", "log-likelihood vs complexity plot"],
            "bic": ["AIC/BIC comparison bar chart", "log-likelihood vs complexity plot"],
            "model comparison": ["AIC/BIC comparison bar chart", "log-likelihood vs complexity plot"],
            "log likelihood": ["AIC/BIC comparison bar chart", "log-likelihood vs complexity plot"],
            "information criteria": ["AIC/BIC comparison bar chart", "log-likelihood vs complexity plot"],
        }

        for keyword, graph_list in keyword_map.items():
            if keyword in topic_lower:
                graphs.extend(graph_list)

        return list(set(graphs)) if graphs else ["relevant statistical plot"]

    def _filter_images_by_required_graphs(self, images: List[ImageInfo],
                                           topic: str,
                                           required_graphs: List[str]) -> Tuple[List[ImageInfo], List[str]]:
        """
        Filter images to match required graphs and identify what's missing.

        Args:
            images: Extracted images to filter
            topic: Study topic
            required_graphs: List of required graph descriptions

        Returns:
            Tuple of (matching images, list of missing graph types)
        """
        if not images or not required_graphs:
            return [], required_graphs

        valid_images = [img for img in images if Path(img.path).exists()]
        if not valid_images:
            return [], required_graphs

        grid_path = self._create_numbered_grid_image(valid_images)
        if not grid_path:
            return [], required_graphs

        graphs_list = "\n".join(f"- {g}" for g in required_graphs)
        prompt = f'''{grid_path}

Look at this numbered grid of images from lecture PDFs. I am studying "{topic}".

I need these graph types:
{graphs_list}

For each image, decide if it is relevant to ANY of the required graphs above.

Respond with ONLY a JSON object:
{{"matches": {{"1": "graph type name", "3": "graph type name"}}, "missing": ["graph types not found"]}}

Where:
- "matches" maps image numbers to which required graph they relate to
- "missing" lists required graphs not found in any image'''

        try:
            result = subprocess.run(
                ['claude', '-p', prompt, '--model', 'opus'],
                capture_output=True,
                text=True,
                timeout=120
            )

            response = result.stdout.strip()
            logger.debug(f"Filter response: {response}")

            # Parse JSON - handle nested structure
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                matches = data.get("matches", {})
                missing = data.get("missing", [])

                # Get matched images
                matched_images = []
                for img_num_str, graph_type in matches.items():
                    try:
                        idx = int(img_num_str) - 1
                        if 0 <= idx < len(valid_images):
                            img = valid_images[idx]
                            img.description = f"Lecture: {graph_type}"
                            matched_images.append(img)
                    except ValueError:
                        continue

                logger.info(f"Found {len(matched_images)} matching images, missing: {missing}")
                return matched_images, missing

        except Exception as e:
            logger.error(f"Error filtering images: {e}")

        finally:
            try:
                Path(grid_path).unlink()
            except:
                pass

        return [], required_graphs

    def filter_images_by_relevance(self, images: List[ImageInfo], topic: str,
                                      batch_size: int = 6) -> List[ImageInfo]:
        """
        Use Haiku vision model via CLI to filter images by relevance to topic.

        Creates a numbered grid image combining all extracted images, sends it
        to Claude Haiku via CLI, and keeps only the images marked as relevant.

        Args:
            images: List of extracted images to filter
            topic: The study topic to check relevance against
            batch_size: Unused, kept for API compatibility

        Returns:
            List of ImageInfo objects that are relevant to the topic
        """
        if not images:
            return []

        # Build list of valid images (those that exist)
        valid_images = []
        for img in images:
            if Path(img.path).exists():
                valid_images.append(img)

        if not valid_images:
            return []

        # Create combined grid image
        grid_path = self._create_numbered_grid_image(valid_images)
        if not grid_path:
            logger.warning("Could not create grid image, returning all images")
            return valid_images

        try:
            # Get relevant indices via CLI
            relevant_indices = self._filter_via_cli(grid_path, topic, len(valid_images))

            # Map indices back to ImageInfo objects (1-indexed to 0-indexed)
            relevant_images = []
            for idx in relevant_indices:
                list_idx = idx - 1
                if 0 <= list_idx < len(valid_images):
                    relevant_images.append(valid_images[list_idx])

            logger.info(f"Relevance filter: {len(relevant_images)}/{len(valid_images)} images kept for '{topic}'")
            return relevant_images

        finally:
            # Clean up temp grid file
            try:
                Path(grid_path).unlink()
            except Exception:
                pass

    def _check_batch_relevance(self, images: List[ImageInfo], topic: str) -> List[ImageInfo]:
        """
        Check relevance of a batch of images using Anthropic API with Haiku vision.

        Args:
            images: Batch of images to check
            topic: Topic to check relevance against

        Returns:
            List of relevant images from the batch
        """
        try:
            import anthropic
        except ImportError:
            logger.warning("anthropic package not installed, skipping relevance filter")
            return images

        valid_images = []
        content_blocks = []

        for idx, img in enumerate(images):
            path = Path(img.path)
            if not path.exists():
                continue

            try:
                # Read and encode image
                with open(path, "rb") as f:
                    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

                # Determine media type
                suffix = path.suffix.lower()
                media_type = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".webp": "image/webp"
                }.get(suffix, "image/png")

                content_blocks.append({
                    "type": "text",
                    "text": f"Image {idx + 1} (from page {img.page}):"
                })
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data
                    }
                })
                valid_images.append((idx, img))

            except Exception as e:
                logger.debug(f"Could not load image {path}: {e}")

        if not valid_images:
            return []

        # Create prompt for Haiku
        prompt_text = f"""You are analyzing lecture slide images to determine if they are relevant to the study topic: "{topic}"

For each image, decide if it is RELEVANT or NOT RELEVANT to studying "{topic}".

An image is RELEVANT if it:
- Shows a graph, chart, or visualization directly related to {topic}
- Contains a formula or equation about {topic}
- Illustrates a concept that is specifically about {topic}
- Shows R code output or statistical results about {topic}

An image is NOT RELEVANT if it:
- Is a university logo, banner, or decorative element
- Shows content about a different statistical topic (e.g., correlation when studying outliers)
- Is a generic diagram not specific to {topic}
- Is too small or unclear to be educational

Respond with ONLY a JSON object (no other text):
{{"relevant": [1, 3, 5]}}

Where the numbers are the image numbers (1-indexed) that ARE relevant.
If none are relevant, respond: {{"relevant": []}}"""

        content_blocks.append({
            "type": "text",
            "text": prompt_text
        })

        try:
            client = anthropic.Anthropic()
            response = client.messages.create(
                model="claude-haiku-4-20250514",
                max_tokens=256,
                messages=[
                    {"role": "user", "content": content_blocks}
                ]
            )

            response_text = response.content[0].text if response.content else ""

            # Parse the JSON response
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                relevant_indices = data.get("relevant", [])

                # Map back to images (1-indexed in response, 0-indexed in list)
                relevant = []
                for rel_idx in relevant_indices:
                    list_idx = rel_idx - 1  # Convert to 0-indexed
                    if 0 <= list_idx < len(valid_images):
                        _, img = valid_images[list_idx]
                        relevant.append(img)

                return relevant
            else:
                logger.warning(f"Could not parse Haiku response: {response_text[:200]}")
                return [img for _, img in valid_images]

        except Exception as e:
            logger.error(f"Error in relevance check: {e}")
            return [img for _, img in valid_images]

    def generate_graphs_for_topic(self, topic: str) -> List[ImageInfo]:
        """Generate statistical graphs appropriate for a topic."""
        topic_hash = self._get_topic_hash(topic)
        topic_dir = self.storage_dir / topic_hash
        topic_dir.mkdir(parents=True, exist_ok=True)

        # Update generator output directory
        self.generator.output_dir = topic_dir

        return self.generator.generate_for_topic(topic)

    def get_images_for_topic(self, topic: str,
                              include_extracted: bool = True,
                              include_generated: bool = True) -> List[ImageInfo]:
        """
        Get all images associated with a topic.

        Args:
            topic: Topic name
            include_extracted: Include images extracted from PDFs
            include_generated: Include generated statistical graphs

        Returns:
            List of ImageInfo objects
        """
        metadata = self._load_metadata()
        topic_lower = topic.lower()

        images = []
        for stored_topic, image_list in metadata.items():
            if stored_topic.lower() == topic_lower:
                for img_data in image_list:
                    info = ImageInfo.from_dict(img_data)
                    if info.source == "extracted" and include_extracted:
                        images.append(info)
                    elif info.source == "generated" and include_generated:
                        images.append(info)

        return images

    def save_images_for_topic(self, topic: str, images: List[ImageInfo]):
        """Save image metadata for a topic."""
        metadata = self._load_metadata()
        metadata[topic] = [img.to_dict() for img in images]
        self._save_metadata(metadata)

    def clear_topic_cache(self, topic: str) -> bool:
        """
        Clear cached images for a topic to force re-search.

        Args:
            topic: Topic name to clear

        Returns:
            True if cache was cleared, False if topic not found
        """
        metadata = self._load_metadata()
        topic_lower = topic.lower()

        # Find and remove matching topic
        topics_to_remove = [t for t in metadata if t.lower() == topic_lower]

        if not topics_to_remove:
            return False

        for t in topics_to_remove:
            # Optionally delete the actual image files
            topic_hash = self._get_topic_hash(t)
            topic_dir = self.storage_dir / topic_hash
            if topic_dir.exists():
                import shutil
                try:
                    shutil.rmtree(topic_dir)
                    logger.info(f"Deleted image directory for '{t}'")
                except Exception as e:
                    logger.warning(f"Could not delete directory {topic_dir}: {e}")

            del metadata[t]

        self._save_metadata(metadata)
        logger.info(f"Cleared cache for topic: {topic}")
        return True

    def clear_all_cache(self):
        """Clear all cached images and metadata."""
        import shutil

        # Clear metadata
        self._save_metadata({})

        # Clear all image directories
        if self.storage_dir.exists():
            for item in self.storage_dir.iterdir():
                if item.is_dir():
                    try:
                        shutil.rmtree(item)
                    except Exception as e:
                        logger.warning(f"Could not delete {item}: {e}")

        logger.info("Cleared all image cache")

    def search_lecture_images_via_rag(self, topic: str) -> Tuple[List[ImageInfo], bool]:
        """
        Search for relevant images in lecture PDFs using RAG system.

        This queries the RAG system to find which lecture PDFs and pages
        are most relevant to the topic, then extracts images from those pages.

        Args:
            topic: The study topic to search for

        Returns:
            Tuple of (list of ImageInfo, bool indicating if images were found)
        """
        if not HAS_RAG:
            logger.debug("RAG not available, skipping lecture image search")
            return [], False

        try:
            # Get relevant PDF sources and pages from RAG
            image_info = retrieve_images_for_topic(topic, n_results=8)
            pdf_sources = image_info.get("pdf_sources", [])

            if not pdf_sources:
                logger.debug(f"No PDF sources found for topic: {topic}")
                return [], False

            extracted_images = []

            for source in pdf_sources[:3]:  # Limit to top 3 most relevant PDFs
                pdf_path = Path(source["path"])
                pages = source.get("pages", [])

                if not pdf_path.exists():
                    logger.debug(f"PDF not found: {pdf_path}")
                    continue

                # Extract images from the relevant pages
                # Only expand to adjacent pages if we have few pages
                # Limit to max 6 pages per PDF to avoid extracting too many images
                expanded_pages = set()
                for page in pages[:4]:  # Limit to top 4 most relevant pages per PDF
                    expanded_pages.add(page)
                    if page > 1 and len(expanded_pages) < 6:
                        expanded_pages.add(page - 1)
                    if len(expanded_pages) < 6:
                        expanded_pages.add(page + 1)

                images = self.extract_images_from_pdf(
                    pdf_path,
                    topic,
                    list(expanded_pages) if expanded_pages else None
                )
                extracted_images.extend(images)

                logger.info(f"Extracted {len(images)} images from {pdf_path.name} pages {sorted(expanded_pages)}")

                # Stop if we have enough images
                if len(extracted_images) >= 15:
                    logger.info(f"Reached image limit, stopping extraction")
                    break

            # Final limit before filtering - keep reasonable number
            if len(extracted_images) > 20:
                # Sort by page number and take first 20 for filtering
                extracted_images.sort(key=lambda x: (x.page or 999))
                extracted_images = extracted_images[:20]
                logger.info(f"Pre-filter trim to {len(extracted_images)} images")

            # Apply relevance filtering using Haiku vision model
            if extracted_images:
                logger.info(f"Filtering {len(extracted_images)} images for relevance to '{topic}'...")
                extracted_images = self.filter_images_by_relevance(extracted_images, topic)

            # Final limit after filtering
            if len(extracted_images) > 8:
                extracted_images = extracted_images[:8]

            return extracted_images, len(extracted_images) > 0

        except Exception as e:
            logger.error(f"Error searching lecture images: {e}")
            return [], False

    def get_or_create_images(self, topic: str, pdf_paths: Optional[List[Path]] = None,
                              relevant_pages: Optional[List[int]] = None,
                              prefer_lecture_images: bool = True) -> List[ImageInfo]:
        """
        Get existing images or create new ones for a topic.

        New workflow:
        1. Check for cached images first
        2. Ask Sonnet: "What graphs are needed to understand this topic?"
        3. Extract images from lecture PDFs
        4. Ask Sonnet: "Which images match the required graphs? What's missing?"
        5. Generate missing graphs with Python (labeled as "Generated")

        Args:
            topic: Topic name
            pdf_paths: Optional list of PDF paths to extract from
            relevant_pages: Optional list of relevant page numbers
            prefer_lecture_images: If True, search RAG for lecture images first

        Returns:
            List of ImageInfo objects
        """
        # Check for existing cached images
        existing = self.get_images_for_topic(topic)
        if existing:
            valid = [img for img in existing if Path(img.path).exists()]
            if valid:
                logger.debug(f"Using {len(valid)} cached images for topic: {topic}")
                return valid

        images = []

        # Step 1: Ask Sonnet what graphs are needed for this topic
        logger.info(f"Getting required graphs for '{topic}'...")
        required_graphs = self._get_required_graphs_for_topic(topic)
        logger.info(f"Required graphs: {required_graphs}")

        # Step 2: Extract images from lecture PDFs
        extracted_images = []
        if prefer_lecture_images and HAS_RAG:
            try:
                image_info = retrieve_images_for_topic(topic, n_results=8)
                pdf_sources = image_info.get("pdf_sources", [])

                for source in pdf_sources[:3]:
                    pdf_path = Path(source["path"])
                    pages = source.get("pages", [])

                    if not pdf_path.exists():
                        continue

                    expanded_pages = set()
                    for page in pages[:4]:
                        expanded_pages.add(page)
                        if page > 1 and len(expanded_pages) < 6:
                            expanded_pages.add(page - 1)
                        if len(expanded_pages) < 6:
                            expanded_pages.add(page + 1)

                    imgs = self.extract_images_from_pdf(pdf_path, topic, list(expanded_pages))
                    extracted_images.extend(imgs)
                    logger.info(f"Extracted {len(imgs)} images from {pdf_path.name}")

                    if len(extracted_images) >= 20:
                        break

            except Exception as e:
                logger.error(f"Error extracting from lectures: {e}")

        # Also extract from manually specified PDFs
        if pdf_paths:
            for pdf_path in pdf_paths:
                if pdf_path.exists():
                    imgs = self.extract_images_from_pdf(pdf_path, topic, relevant_pages)
                    extracted_images.extend(imgs)

        # Step 3: Filter images to match required graphs
        # Limit to 20 images for grid (too many overwhelms vision model)
        if len(extracted_images) > 20:
            extracted_images = extracted_images[:20]

        missing_graphs = required_graphs
        if extracted_images:
            logger.info(f"Filtering {len(extracted_images)} images against required graphs...")
            matched_images, missing_graphs = self._filter_images_by_required_graphs(
                extracted_images, topic, required_graphs
            )
            images.extend(matched_images)
            logger.info(f"Found {len(matched_images)} matching lecture images")

        # Step 4: Generate missing graphs
        if missing_graphs:
            logger.info(f"Generating {len(missing_graphs)} missing graphs: {missing_graphs}")
            generated = self._generate_missing_graphs(topic, missing_graphs)
            images.extend(generated)

        # Save metadata for caching
        if images:
            self.save_images_for_topic(topic, images)
            extracted_count = sum(1 for i in images if i.source == 'extracted')
            generated_count = sum(1 for i in images if i.source == 'generated')
            logger.info(f"Total: {len(images)} images ({extracted_count} from lectures, {generated_count} generated)")

        return images

    def _generate_missing_graphs(self, topic: str, missing_graphs: List[str]) -> List[ImageInfo]:
        """Generate graphs for types not found in lectures."""
        topic_hash = self._get_topic_hash(topic)
        topic_dir = self.storage_dir / topic_hash
        topic_dir.mkdir(parents=True, exist_ok=True)

        self.generator.output_dir = topic_dir
        generated = []
        topic_lower = topic.lower()

        # For assumption topics, use comparison graphs showing good vs violated
        is_assumption_topic = "assumption" in topic_lower

        # Track what we've already generated to avoid duplicates
        generated_types = set()

        for graph_desc in missing_graphs:
            graph_lower = graph_desc.lower()
            img = None

            try:
                # For assumption topics, prioritize comparison graphs
                if is_assumption_topic:
                    # Check normality first (histogram, q-q) before residual
                    if any(kw in graph_lower for kw in ["q-q", "qq", "histogram", "normal", "skew"]):
                        if "assumption_normality" not in generated_types:
                            img = self.generator.assumption_normality_comparison(topic)
                            generated_types.add("assumption_normality")

                    elif any(kw in graph_lower for kw in ["residual", "fitted", "homoscedastic", "heteroscedastic", "linearity", "scale-location"]):
                        if "assumption_residual" not in generated_types:
                            img = self.generator.assumption_residual_comparison(topic)
                            generated_types.add("assumption_residual")

                    elif any(kw in graph_lower for kw in ["independence", "autocorr", "order"]):
                        if "assumption_independence" not in generated_types:
                            img = self.generator.assumption_independence_comparison(topic)
                            generated_types.add("assumption_independence")

                # Fallback to standard graphs if not assumption topic or no match
                if img is None:
                    if any(kw in graph_lower for kw in ["residual", "fitted"]):
                        img = self.generator.residual_plot(topic)

                    elif any(kw in graph_lower for kw in ["q-q", "qq", "normal prob"]):
                        img = self.generator.normal_distribution(topic)

                    elif any(kw in graph_lower for kw in ["scatter", "regression line", "linear"]):
                        img = self.generator.regression_example(topic)

                    elif any(kw in graph_lower for kw in ["boxplot", "box plot", "anova"]):
                        img = self.generator.anova_boxplot(topic)

                    elif any(kw in graph_lower for kw in ["histogram"]):
                        img = self.generator.normal_distribution(topic)

                    elif any(kw in graph_lower for kw in ["correlation", "heatmap"]):
                        img = self.generator.correlation_matrix(topic)

                    elif any(kw in graph_lower for kw in ["confidence", "interval"]):
                        img = self.generator.confidence_interval(topic)

                    elif any(kw in graph_lower for kw in ["t-dist", "t dist"]):
                        img = self.generator.t_distribution(topic)

                    elif any(kw in graph_lower for kw in ["sampling", "central limit"]):
                        img = self.generator.sampling_distribution(topic)

                    elif any(kw in graph_lower for kw in ["aic", "bic", "model comparison", "information criteria", "log-likelihood", "log likelihood", "model selection"]):
                        img = self.generator.model_comparison(topic)

                if img:
                    img.description = f"Generated: {graph_desc}"
                    generated.append(img)

            except Exception as e:
                logger.error(f"Error generating '{graph_desc}': {e}")

        return generated


# Convenience function for use in study_session.py
def get_graphs_for_study_topic(topic: str, colors: Optional[Dict] = None,
                                prefer_lecture_images: bool = True) -> List[ImageInfo]:
    """
    Get or generate graphs for a study topic.

    Enhanced workflow:
    1. First searches RAG system for relevant figures in lecture PDFs
    2. Extracts images from the most relevant lecture pages
    3. Falls back to generating statistical visualizations if none found
    4. May supplement lecture images with generated graphs for completeness

    Args:
        topic: The topic being studied
        colors: Optional theme colors for graph styling
        prefer_lecture_images: If True (default), prioritize images from lectures

    Returns:
        List of ImageInfo objects (may include both extracted and generated images)
    """
    manager = GraphManager(colors=colors)
    return manager.get_or_create_images(topic, prefer_lecture_images=prefer_lecture_images)
