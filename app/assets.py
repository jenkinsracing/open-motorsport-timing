from flask_assets import Bundle

common_css = Bundle(
    'css/vendor/bootstrap.css',
    'css/vendor/bootstrap-table.css',
    'css/vendor/bootstrap-table-filter-control.css',
    'css/vendor/jquery-ui.css',
    'css/vendor/jquery-ui.structure.css',
    'css/vendor/jquery-ui.theme.css',
    'css/vendor/bootstrap-tokenfield.css',
    'css/vendor/helper.css',
    'css/main.css',
    filters='cssmin',
    output='public/css/common.css'
)

common_js = Bundle(
    'js/vendor/jquery.js',
    'js/vendor/bootstrap.js',
    'js/vendor/bootstrap-table.js',
    'js/vendor/bootstrap-table-cookie.js',
    'js/vendor/bootstrap-table-mobile.js',
    'js/vendor/bootstrap-table-export.js',
    'js/vendor/bootstrap-table-filter-control.js',
    'js/vendor/Chart.js',
    'js/vendor/jquery.nicescroll.js',
    'js/vendor/jquery-ui.js',
    'js/vendor/bootstrap-tokenfield.js',
    Bundle(
        'js/main.js',
        filters='jsmin'
    ),
    output='public/js/common.js'
)

sitereports_js = Bundle('js/sitereports.js', filters='jsmin', output='public/js/sitereports.js')
tablebase_js = Bundle('js/tablebase.js', filters='jsmin', output='public/js/tablebase.js')
dashboard_js = Bundle('js/dashboard.js', filters='jsmin', output='public/js/dashboard.js')
devices_js = Bundle('js/devices.js', filters='jsmin', output='public/js/devices.js')
devices_bar_js = Bundle('js/devices-bar.js', filters='jsmin', output='public/js/devices-bar.js')
ios_js = Bundle('js/ios.js', filters='jsmin', output='public/js/ios.js')
ios_pie_js = Bundle('js/ios-pie.js', filters='jsmin', output='public/js/ios-pie.js')
