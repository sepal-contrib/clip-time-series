from pathlib import Path
import shutil
import tempfile
from component.scripts.export import get_pdf
from component.scripts.gee import get_gee_vrt
from component.scripts.planet import get_planet_vrt
from component.scripts.utils import get_pdf_path, get_vrt_filename


def test_get_gee_pdf(geometries, alert):

    try:
        tmp_dir = Path(tempfile.mkdtemp())
        input_file_path = tmp_dir / "test_points.csv"
        mosaics = [2024]
        image_size = 10000
        sources = ["landsat"]
        bands = "Red, Green, Blue"
        square_size = 90

        pdf_filepath = get_pdf_path(
            input_file_path.stem, sources, bands, square_size, image_size
        )

        vrt_list, title_list = get_gee_vrt(
            geometries,
            mosaics,
            image_size,
            pdf_filepath.stem,
            bands,
            sources,
            alert,
            tmp_dir,
        )

        pdf_file = get_pdf(
            pdf_filepath=pdf_filepath,
            mosaics=mosaics,
            image_size=image_size,
            square_size=square_size,
            vrt_list=vrt_list,
            title_list=title_list,
            band_combo=bands,
            geometry=geometries,
            output=alert,
            tmp_dir=tmp_dir,
        )

        assert pdf_file == pdf_filepath
        assert pdf_file.is_file()

    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tmp_dir)


def test_get_planet_pdf(geometries, alert, planet_model):

    try:
        tmp_dir = Path(tempfile.mkdtemp())
        input_file_path = tmp_dir / "test_points.csv"

        mosaics = [
            "planet_medres_normalized_analytic_2020-10_mosaic",
            "planet_medres_normalized_analytic_2020-09_mosaic",
        ]

        size = 250
        sources = ["planet"]
        bands = "cir"
        square_size = 90

        pdf_filepath = get_pdf_path(
            input_file_path.stem, sources, bands, size, "min_max"
        )

        vrt_filename = get_vrt_filename(input_file_path.stem, sources, bands, size)

        vrt_list, title_list = get_planet_vrt(
            geometry=geometries,
            mosaics=mosaics,
            size=size,
            filename=vrt_filename,
            bands=bands,
            out=alert,
            tmp_dir=tmp_dir,
            planet_model=planet_model,
        )

        pdf_file = get_pdf(
            pdf_filepath=pdf_filepath,
            mosaics=mosaics,
            image_size=size,
            square_size=square_size,
            vrt_list=vrt_list,
            title_list=title_list,
            band_combo=bands,
            geometry=geometries,
            output=alert,
            tmp_dir=tmp_dir,
            enhance_method="min_max",
        )
        print("#####", pdf_file)

        assert pdf_file == pdf_filepath
        assert pdf_file.is_file()

    except Exception as e:
        raise e
    finally:
        shutil.rmtree(tmp_dir)
