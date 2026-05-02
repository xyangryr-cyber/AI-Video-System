"""Tests for [SPEC-F-005] React Community Components: News Card, Quote Card, Policy Comparison."""

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"
TEMPLATE_DIR = FRONTEND_DIR / "components" / "templates" / "react"
REGISTRY_PATH = FRONTEND_DIR / "components" / "templates" / "template_registry.ts"
PACKAGE_JSON_PATH = FRONTEND_DIR / "package.json"


def _read_text(path: Path) -> str:
    assert path.is_file(), f"Missing file: {path}"
    return path.read_text(encoding="utf-8")


class TestAC1NewsCardStaggerChildren:
    """AC-1: `news_card` uses Framer Motion `<motion.div>` slide-in + `staggerChildren` for line-by-line fade-in"""

    def test_news_card_file_exists(self):
        news_card_path = TEMPLATE_DIR / "NewsCard.tsx"
        assert news_card_path.is_file(), f"NewsCard.tsx not found at {news_card_path}"

    def test_news_card_has_motion_div(self):
        source = _read_text(TEMPLATE_DIR / "NewsCard.tsx")
        assert re.search(r"motion\.div", source), (
            "NewsCard.tsx must contain motion.div for slide-in animation"
        )

    def test_news_card_has_stagger_children(self):
        source = _read_text(TEMPLATE_DIR / "NewsCard.tsx")
        assert re.search(r"staggerChildren", source), (
            "NewsCard.tsx must use staggerChildren for line-by-line fade-in"
        )


class TestAC2NewsCardLottieSentiment:
    """AC-2: `news_card` uses Lottie for sentiment icon animation"""

    def test_news_card_imports_lottie(self):
        source = _read_text(TEMPLATE_DIR / "NewsCard.tsx")
        assert re.search(r"from ['\"]lottie-react['\"]", source) or re.search(
            r"import.*Lottie.*from", source
        ), "NewsCard.tsx must import from lottie-react for sentiment icon animation"

    def test_news_card_uses_lottie_component(self):
        source = _read_text(TEMPLATE_DIR / "NewsCard.tsx")
        assert re.search(r"<Lottie", source), (
            "NewsCard.tsx must render <Lottie> component for sentiment icon"
        )


class TestAC3QuoteCardWordByWord:
    """AC-3: `quote_card` uses `<motion.span>` for word-by-word display"""

    def test_quote_card_file_exists(self):
        quote_card_path = TEMPLATE_DIR / "QuoteCard.tsx"
        assert quote_card_path.is_file(), (
            f"QuoteCard.tsx not found at {quote_card_path}"
        )

    def test_quote_card_has_motion_span(self):
        source = _read_text(TEMPLATE_DIR / "QuoteCard.tsx")
        assert re.search(r"motion\.span", source), (
            "QuoteCard.tsx must contain motion.span for word-by-word display"
        )

    def test_quote_card_splits_words(self):
        source = _read_text(TEMPLATE_DIR / "QuoteCard.tsx")
        assert re.search(r"\.split\(", source), (
            "QuoteCard.tsx must split text into words for word-by-word animation"
        )


class TestAC4QuoteCardLottieQuotation:
    """AC-4: `quote_card` uses Lottie for quotation mark expand animation"""

    def test_quote_card_imports_lottie(self):
        source = _read_text(TEMPLATE_DIR / "QuoteCard.tsx")
        assert re.search(r"from ['\"]lottie-react['\"]", source) or re.search(
            r"import.*Lottie.*from", source
        ), "QuoteCard.tsx must import from lottie-react for quotation mark animation"

    def test_quote_card_uses_lottie_component(self):
        source = _read_text(TEMPLATE_DIR / "QuoteCard.tsx")
        assert re.search(r"<Lottie", source), (
            "QuoteCard.tsx must render <Lottie> component for quotation mark animation"
        )


class TestAC5PolicyComparisonAnimatePresence:
    """AC-5: `policy_comparison` uses `<AnimatePresence>` + `layout` animation for row-by-row fill"""

    def test_policy_comparison_file_exists(self):
        path = TEMPLATE_DIR / "PolicyComparison.tsx"
        assert path.is_file(), f"PolicyComparison.tsx not found at {path}"

    def test_policy_comparison_has_animate_presence(self):
        source = _read_text(TEMPLATE_DIR / "PolicyComparison.tsx")
        assert re.search(r"AnimatePresence", source), (
            "PolicyComparison.tsx must use AnimatePresence for enter/exit animations"
        )

    def test_policy_comparison_has_layout_anim(self):
        source = _read_text(TEMPLATE_DIR / "PolicyComparison.tsx")
        assert re.search(r"layout", source), (
            "PolicyComparison.tsx must use layout animation for row-by-row fill"
        )


class TestAC6PolicyComparisonHighlightRow:
    """AC-6: `policy_comparison` uses `<motion.tr>` for highlight row scale"""

    def test_policy_comparison_has_motion_tr(self):
        source = _read_text(TEMPLATE_DIR / "PolicyComparison.tsx")
        assert re.search(r"motion\.tr", source), (
            "PolicyComparison.tsx must contain motion.tr for highlight row animation"
        )


class TestAC7AllImplementTemplateProps:
    """AC-7: All 3 implement `React.FC<TemplateProps>` and are registered in `template_registry.ts`"""

    def test_registry_file_exists(self):
        assert REGISTRY_PATH.is_file(), (
            f"template_registry.ts not found at {REGISTRY_PATH}"
        )

    def test_news_card_registered(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(r"NewsCard", source), (
            "template_registry.ts must reference NewsCard"
        )

    def test_quote_card_registered(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(r"QuoteCard", source), (
            "template_registry.ts must reference QuoteCard"
        )

    def test_policy_comparison_registered(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(r"PolicyComparison", source), (
            "template_registry.ts must reference PolicyComparison"
        )

    def test_template_props_imported(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(r"TemplateProps", source), (
            "template_registry.ts must import TemplateProps for type annotation"
        )

    def test_all_implement_fc_template_props(self):
        for name in ("NewsCard", "QuoteCard", "PolicyComparison"):
            path = TEMPLATE_DIR / f"{name}.tsx"
            source = _read_text(path)
            assert re.search(r"TemplateProps", source), (
                f"{name}.tsx must reference TemplateProps in its type signature"
            )


class TestAC8NoExcludedDependencies:
    """AC-8: No `react-vertical-timeline` or `react-force-graph` in dependencies"""

    def test_no_excluded_deps(self):
        pkg = json.loads(_read_text(PACKAGE_JSON_PATH))
        all_deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        excluded = ["react-vertical-timeline", "react-force-graph"]
        for dep in excluded:
            assert dep not in all_deps, (
                f"Forbidden dependency '{dep}' found in package.json"
            )
