import ipyvuetify as v
import solara
import solara.server.settings
from sepal_ui.mapping import SepalMap
from sepal_ui.scripts.utils import init_ee
from sepal_ui.sepalwidgets.vue_app import MapApp, ThemeToggle
from solara.lab.components.theming import theme

from component import parameter as cp

init_ee()
from sepal_ui import sepalwidgets as sw
from sepal_ui.planetapi import PlanetView

from component import model, tile

init_ee()


# solara.server.settings.main.root_path = "/api/app-launcher/seplan"
solara.server.settings.assets.fontawesome_path = (
    "/@fortawesome/fontawesome-free@6.7.2/css/all.min.css"
)
solara.server.settings.assets.extra_locations = ["./assets/"]


@solara.component
def Page():

    # This we have to create here because we need to pass it to all the maps
    # which doesn't have a builtin method to change the theme
    theme_toggle = ThemeToggle()
    theme_toggle.observe(lambda e: setattr(theme, "dark", e["new"]), "dark")

    solara.lab.theme.themes.dark.primary = "#76591e"
    solara.lab.theme.themes.dark.primary_contrast = "#bf8f2d"
    solara.lab.theme.themes.dark.secondary = "#363e4f"
    solara.lab.theme.themes.dark.secondary_contrast = "#5d76ab"
    solara.lab.theme.themes.dark.error = "#a63228"
    solara.lab.theme.themes.dark.info = "#c5c6c9"
    solara.lab.theme.themes.dark.success = "#3f802a"
    solara.lab.theme.themes.dark.warning = "#b8721d"
    solara.lab.theme.themes.dark.accent = "#272727"
    solara.lab.theme.themes.dark.anchor = "#f3f3f3"
    solara.lab.theme.themes.dark.main = "#24221f"
    solara.lab.theme.themes.dark.darker = "#1a1a1a"
    solara.lab.theme.themes.dark.bg = "#121212"
    solara.lab.theme.themes.dark.menu = "#424242"

    solara.lab.theme.themes.light.primary = "#5BB624"
    solara.lab.theme.themes.light.primary_contrast = "#76b353"
    solara.lab.theme.themes.light.accent = "#f3f3f3"
    solara.lab.theme.themes.light.anchor = "#f3f3f3"
    solara.lab.theme.themes.light.secondary = "#2199C4"
    solara.lab.theme.themes.light.secondary_contrast = "#5d76ab"
    solara.lab.theme.themes.light.main = "#2196f3"
    solara.lab.theme.themes.light.darker = "#ffffff"
    solara.lab.theme.themes.light.bg = "#FFFFFF"
    solara.lab.theme.themes.light.menu = "#FFFFFF"

    map_ = SepalMap([cp.basemap], fullscreen=True, min_zoom=3)

    ts_about = sw.TileAbout("utils/about.md")
    ts_disclaimer = sw.TileDisclaimer()

    tb_model = model.TableModel()

    # output to display messages
    file_tile = tile.FileTile(tb_model, map_)

    # create a test downloader
    test_tile = tile.TestTile(file_tile)

    planet_view = PlanetView()
    viz_model = model.VizModel()
    viz_input_tile = tile.InputTile(viz_model, tb_model, planet_view=planet_view)

    export_model = model.ExportModel()
    # result tile
    export_results = tile.ExportResult()
    # export data
    export_tile = tile.ExportData(
        export_model,
        viz_model,
        tb_model,
        export_results,
        planet_model=planet_view.planet_model,
    )

    import_points_tile = v.Flex(
        children=[
            test_tile,
            file_tile,
        ]
    )

    export_tile = v.Flex(
        children=[
            export_tile,
            export_results,
        ]
    )

    disclaimer_tile = v.Flex(
        children=[
            ts_disclaimer,
            ts_about,
        ]
    )

    steps_data = [
        {
            "id": 2,
            "name": "Import points",
            "icon": "mdi-map-marker-check",
            "display": "dialog",
            "actions": [
                {"label": "Cancel", "close": True, "cancel": True},
                {"label": "Next", "next": 3},
            ],
        },
        {
            "id": 3,
            "name": "Visualize points",
            "icon": "mdi-earth",
            "display": "dialog",
            "actions": [
                {"label": "Cancel", "close": True, "cancel": True},
                {"label": "Prev", "next": 2},
                {"label": "Next", "next": 4},
            ],
        },
        {
            "id": 4,
            "name": "Export data",
            "icon": "mdi-export",
            "display": "dialog",
            "actions": [
                {"label": "Cancel", "close": True, "cancel": True},
                {"label": "Prev", "next": 3},
                {"label": "Apply", "close": True},
            ],
        },
        {
            "id": 5,
            "name": "About",
            "icon": "mdi-help-circle",
            "display": "step",
        },
    ]

    steps_content = [import_points_tile, viz_input_tile, export_tile, disclaimer_tile]

    MapApp.element(
        app_title="Clip time series",
        app_icon="mdi-satellite",
        main_map=[map_],
        steps_data=steps_data,
        steps_content=steps_content,
        theme_toggle=[theme_toggle],
        repo_url="https://github.com/sepal-contrib/clip-time-series",
    )
