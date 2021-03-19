from importlib import import_module

modules = ['auth', 'booking']


def init_app(app):
    for module in modules:
        app.register_blueprint(import_module(
            '.' + module, package='bookB116.api').bp)
