"""
Helper functions for Altair chart theming.
Provides consistent configuration across all charts.
"""
import altair as alt


def get_tooltip_config(is_dark_mode: bool) -> dict:
    """
    Retorna la configuración de tooltip para Altair basada en el tema.
    
    Args:
        is_dark_mode (bool): True para modo oscuro, False para modo claro
    
    Returns:
        dict: Configuración de tooltip para .configure_mark()
    """
    if is_dark_mode:
        return {
            "tooltip": {
                "content": "data",
                "style": {
                    "backgroundColor": "#1F2937",
                    "color": "#FFFFFF",
                    "borderColor": "#374151",
                    "fontSize": 12
                }
            }
        }
    else:
        return {
            "tooltip": {
                "content": "data",
                "style": {
                    "backgroundColor": "#FFFFFF",
                    "color": "#000000",
                    "borderColor": "#E5E7EB",
                    "fontSize": 12
                }
            }
        }


def get_axis_config(is_dark_mode: bool) -> dict:
    """
    Configuración de ejes para Altair.
    
    Args:
        is_dark_mode (bool): True para modo oscuro, False para modo claro
    
    Returns:
        dict: Configuración de axis
    """
    text_color = "#FFFFFF" if is_dark_mode else "#000000"
    grid_color = "#374151" if is_dark_mode else "#E5E7EB"
    
    return {
        "labelColor": text_color,
        "titleColor": text_color,
        "gridColor": grid_color,
        "domainColor": grid_color,
        "tickColor": grid_color,
        "labelFontSize": 11,
        "titleFontSize": 12
    }


def get_legend_config(is_dark_mode: bool) -> dict:
    """
    Configuración de leyenda para Altair.
    
    Args:
        is_dark_mode (bool): True para modo oscuro, False para modo claro
    
    Returns:
        dict: Configuración de legend
    """
    text_color = "#FFFFFF" if is_dark_mode else "#000000"
    
    return {
        "labelColor": text_color,
        "titleColor": text_color,
        "labelFontSize": 11,
        "titleFontSize": 12,
        "orient": "right",
        "direction": "vertical"
    }


def get_title_params(title_text: str, is_dark_mode: bool) -> alt.TitleParams:
    """
    Crea un TitleParams con el color apropiado.
    
    Args:
        title_text (str): Texto del título
        is_dark_mode (bool): True para modo oscuro, False para modo claro
    
    Returns:
        alt.TitleParams: Configuración del título
    """
    text_color = "#FFFFFF" if is_dark_mode else "#000000"
    return alt.TitleParams(title_text, color=text_color, fontSize=14)


def configure_chart_theme(chart: alt.Chart, is_dark_mode: bool) -> alt.Chart:
    """
    Aplica configuración completa de tema a un gráfico de Altair.
    Incluye tooltips, ejes, leyendas y formateo general.
    
    Args:
        chart (alt.Chart): Gráfico de Altair
        is_dark_mode (bool): True para modo oscuro, False para modo claro
    
    Returns:
        alt.Chart: Gráfico configurado
    """
    bg_color = "transparent"
    text_color = "#FFFFFF" if is_dark_mode else "#000000"
    
    return chart.configure(
        background=bg_color
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        **get_axis_config(is_dark_mode)
    ).configure_legend(
        **get_legend_config(is_dark_mode)
    ).configure_title(
        color=text_color,
        fontSize=14,
        anchor='start'
    )
