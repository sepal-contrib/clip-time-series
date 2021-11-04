import traitlets

import ipyvuetify as v


def set_msg(
    pts, bands_combo, sources, basename, mosaics, image_size, square_size, driver
):

    # transform sources in a str
    source_name = " & ".join(sources) if type(sources) == list else None

    nb_pts = len(pts)

    # compute the surface
    pts_conform = pts.to_crs("ESRI:54009")
    minx, miny, maxx, maxy = pts_conform.total_bounds
    surface = (maxx - minx) * (maxy - miny) / 10e6  # in km2

    msg = f"""
        <div>
            <p>
                You're about to launch the following downloading :
            <p>
            <ul>
                <li>
                    <b>{nb_pts}</b> points distributed on <b>{surface:.2f}</b> km\u00B2
                </li>
                <li>
                    Using the images coming from <b>{source_name if source_name else driver}</b>
                <li>
                    Using the <b>{bands_combo}</b> band combination
                </li>
                <li>
                    Using <b>{len(mosaics)}</b> different mosaics
                </li>
                <li>
                    Using thumbnails of <b>{image_size}x{image_size}</b> m\u00B2
                </li>
                <li>
                    Displaying squares of <b>{square_size}x{square_size}</b> m\u00B2  
                </li>
                <li>
                    Saved in a file using <b>{basename}</b> as a basename
                </li>
            </ul>
            
            <p>
                If you agree with these input you can start the downloading, if not please change the inputs in the previous panels
            </p>
        </div>
    """

    # create a Html widget
    class MyHTML(v.VuetifyTemplate):
        template = traitlets.Unicode(msg).tag(sync=True)

    return MyHTML()
