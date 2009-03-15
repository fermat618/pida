from pida.services.plugins.uploader import upload_plugin, register_plugin

register_plugin('pida-plugins', 'man')
upload_plugin('pida-plugins', 'man')
