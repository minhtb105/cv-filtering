"""
Template Manager: Defines and applies TopCV template styles
"""
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum


class TemplateStyle(Enum):
    """TopCV popular template styles"""
    # Modern & Contemporary
    BRIGHT = "Bright"
    MODERN_2 = "Modern 2"
    MODERN_6 = "Modern 6"
    CLARITY = "Clarity"
    ELEGANT = "Elegant"
    ABSTRACTION = "Abstraction"
    CIRCUM = "Circum"
    
    # Minimalist
    MINIMALIST_2 = "Minimalist 2"
    MINIMALIST_6 = "Minimalist 6"
    MINIMALIST_7 = "Minimalist 7"
    SIMPLICATED = "Simplicated"
    MINIMALISM = "Minimalism"
    
    # Creative & Stylish
    CREATIVE = "Creative"
    PASSION = "Passion"
    DELUXE = "Deluxe"
    STYLE_3 = "Style 3"
    STYLE_4 = "Style 4"
    HIGHLIGHT_3 = "Highlight 3"
    
    # Professional & Classic
    TIMELINE = "Timeline"
    SUCCESS = "Success"
    GRAPHITE = "Graphite"
    SMOKY = "Smoky"
    CLOUDY = "Cloudy"
    BORDEAUX = "Bordeaux"
    SIERRA_BLUE = "Sierra Blue"
    CERULEAN_BLUE = "Cerulean Blue"
    DASHED = "Dashed"
    PASTEL = "Pastel"
    SHABBY_CHIC = "Shabby Chic"


@dataclass
class TemplateConfig:
    """Template configuration for DOCX styling"""
    style_id: TemplateStyle
    name: str
    description: str
    color_primary: str  # Hex color
    color_secondary: str
    font_main: str
    font_header: str
    has_sidebar: bool
    has_color_blocks: bool
    layout_type: str  # "modern", "minimalist", "creative", "classic"


class TemplateManager:
    """Manages CV template styles and metadata"""
    
    # Define 22 popular TopCV templates
    TEMPLATES = {
        TemplateStyle.BRIGHT: TemplateConfig(
            style_id=TemplateStyle.BRIGHT,
            name="Bright",
            description="Modern bright design with clean sections",
            color_primary="#FF6B35",
            color_secondary="#F7931E",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=False,
            has_color_blocks=True,
            layout_type="modern"
        ),
        TemplateStyle.MODERN_2: TemplateConfig(
            style_id=TemplateStyle.MODERN_2,
            name="Modern 2",
            description="Contemporary two-column layout",
            color_primary="#2E86AB",
            color_secondary="#A23B72",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=True,
            has_color_blocks=True,
            layout_type="modern"
        ),
        TemplateStyle.MODERN_6: TemplateConfig(
            style_id=TemplateStyle.MODERN_6,
            name="Modern 6",
            description="Six-section modern layout",
            color_primary="#1F77B4",
            color_secondary="#FF7F0E",
            font_main="Arial",
            font_header="Arial",
            has_sidebar=False,
            has_color_blocks=True,
            layout_type="modern"
        ),
        TemplateStyle.CLARITY: TemplateConfig(
            style_id=TemplateStyle.CLARITY,
            name="Clarity",
            description="Clear and simple organization",
            color_primary="#333333",
            color_secondary="#666666",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=False,
            has_color_blocks=False,
            layout_type="classic"
        ),
        TemplateStyle.ELEGANT: TemplateConfig(
            style_id=TemplateStyle.ELEGANT,
            name="Elegant",
            description="Elegant professional design",
            color_primary="#2C3E50",
            color_secondary="#34495E",
            font_main="Georgia",
            font_header="Georgia",
            has_sidebar=True,
            has_color_blocks=False,
            layout_type="classic"
        ),
        TemplateStyle.ABSTRACTION: TemplateConfig(
            style_id=TemplateStyle.ABSTRACTION,
            name="Abstraction",
            description="Abstract geometric design",
            color_primary="#9B59B6",
            color_secondary="#8E44AD",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=True,
            has_color_blocks=True,
            layout_type="creative"
        ),
        TemplateStyle.CIRCUM: TemplateConfig(
            style_id=TemplateStyle.CIRCUM,
            name="Circum",
            description="Circular design elements",
            color_primary="#E74C3C",
            color_secondary="#C0392B",
            font_main="Arial",
            font_header="Arial",
            has_sidebar=False,
            has_color_blocks=True,
            layout_type="creative"
        ),
        TemplateStyle.MINIMALIST_2: TemplateConfig(
            style_id=TemplateStyle.MINIMALIST_2,
            name="Minimalist 2",
            description="Clean minimalist design",
            color_primary="#000000",
            color_secondary="#555555",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=False,
            has_color_blocks=False,
            layout_type="minimalist"
        ),
        TemplateStyle.MINIMALIST_6: TemplateConfig(
            style_id=TemplateStyle.MINIMALIST_6,
            name="Minimalist 6",
            description="Six-section minimal layout",
            color_primary="#1A1A1A",
            color_secondary="#333333",
            font_main="Arial",
            font_header="Arial",
            has_sidebar=False,
            has_color_blocks=False,
            layout_type="minimalist"
        ),
        TemplateStyle.MINIMALIST_7: TemplateConfig(
            style_id=TemplateStyle.MINIMALIST_7,
            name="Minimalist 7",
            description="Seven-section minimalist layout",
            color_primary="#2C2C2C",
            color_secondary="#555555",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=False,
            has_color_blocks=False,
            layout_type="minimalist"
        ),
        TemplateStyle.SIMPLICATED: TemplateConfig(
            style_id=TemplateStyle.SIMPLICATED,
            name="Simplicated",
            description="Simplified sophisticated design",
            color_primary="#404040",
            color_secondary="#808080",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=False,
            has_color_blocks=False,
            layout_type="minimalist"
        ),
        TemplateStyle.MINIMALISM: TemplateConfig(
            style_id=TemplateStyle.MINIMALISM,
            name="Minimalism",
            description="Pure minimalism design",
            color_primary="#000000",
            color_secondary="#CCCCCC",
            font_main="Arial",
            font_header="Arial",
            has_sidebar=False,
            has_color_blocks=False,
            layout_type="minimalist"
        ),
        TemplateStyle.CREATIVE: TemplateConfig(
            style_id=TemplateStyle.CREATIVE,
            name="Creative",
            description="Creative and artistic design",
            color_primary="#FF1493",
            color_secondary="#FFB6C1",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=True,
            has_color_blocks=True,
            layout_type="creative"
        ),
        TemplateStyle.PASSION: TemplateConfig(
            style_id=TemplateStyle.PASSION,
            name="Passion",
            description="Passionate energetic design",
            color_primary="#FF6347",
            color_secondary="#FFB347",
            font_main="Arial",
            font_header="Arial",
            has_sidebar=False,
            has_color_blocks=True,
            layout_type="creative"
        ),
        TemplateStyle.DELUXE: TemplateConfig(
            style_id=TemplateStyle.DELUXE,
            name="Deluxe",
            description="Luxurious professional design",
            color_primary="#4B0082",
            color_secondary="#8B008B",
            font_main="Georgia",
            font_header="Georgia",
            has_sidebar=True,
            has_color_blocks=True,
            layout_type="classic"
        ),
        TemplateStyle.STYLE_3: TemplateConfig(
            style_id=TemplateStyle.STYLE_3,
            name="Style 3",
            description="Stylish modern design",
            color_primary="#20B2AA",
            color_secondary="#48D1CC",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=True,
            has_color_blocks=True,
            layout_type="modern"
        ),
        TemplateStyle.STYLE_4: TemplateConfig(
            style_id=TemplateStyle.STYLE_4,
            name="Style 4",
            description="Stylish contemporary design",
            color_primary="#228B22",
            color_secondary="#90EE90",
            font_main="Arial",
            font_header="Arial",
            has_sidebar=False,
            has_color_blocks=True,
            layout_type="modern"
        ),
        TemplateStyle.HIGHLIGHT_3: TemplateConfig(
            style_id=TemplateStyle.HIGHLIGHT_3,
            name="Highlight 3",
            description="Highlighted key information",
            color_primary="#FFD700",
            color_secondary="#FFA500",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=False,
            has_color_blocks=True,
            layout_type="creative"
        ),
        TemplateStyle.TIMELINE: TemplateConfig(
            style_id=TemplateStyle.TIMELINE,
            name="Timeline",
            description="Timeline-based layout",
            color_primary="#1E90FF",
            color_secondary="#87CEEB",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=False,
            has_color_blocks=True,
            layout_type="modern"
        ),
        TemplateStyle.SUCCESS: TemplateConfig(
            style_id=TemplateStyle.SUCCESS,
            name="Success",
            description="Success-oriented design",
            color_primary="#32CD32",
            color_secondary="#00FF00",
            font_main="Arial",
            font_header="Arial",
            has_sidebar=True,
            has_color_blocks=True,
            layout_type="modern"
        ),
        TemplateStyle.GRAPHITE: TemplateConfig(
            style_id=TemplateStyle.GRAPHITE,
            name="Graphite",
            description="Graphite grey professional design",
            color_primary="#36454F",
            color_secondary="#808080",
            font_main="Calibri",
            font_header="Calibri",
            has_sidebar=False,
            has_color_blocks=False,
            layout_type="classic"
        ),
        TemplateStyle.SMOKY: TemplateConfig(
            style_id=TemplateStyle.SMOKY,
            name="Smoky",
            description="Smoky dark design",
            color_primary="#2F4F4F",
            color_secondary="#708090",
            font_main="Arial",
            font_header="Arial",
            has_sidebar=True,
            has_color_blocks=False,
            layout_type="classic"
        ),
    }
    
    @staticmethod
    def get_all_templates() -> Dict[TemplateStyle, TemplateConfig]:
        """Get all available templates"""
        return TemplateManager.TEMPLATES
    
    @staticmethod
    def get_template(style: TemplateStyle) -> TemplateConfig:
        """Get specific template configuration"""
        return TemplateManager.TEMPLATES.get(style)
    
    @staticmethod
    def get_template_list() -> List[str]:
        """Get list of all template names"""
        return [config.name for config in TemplateManager.TEMPLATES.values()]
    
    @staticmethod
    def get_template_count() -> int:
        """Get total number of templates"""
        return len(TemplateManager.TEMPLATES)
    
    @staticmethod
    def get_templates_by_layout(layout_type: str) -> List[TemplateConfig]:
        """Get templates filtered by layout type"""
        return [
            config for config in TemplateManager.TEMPLATES.values()
            if config.layout_type == layout_type
        ]
