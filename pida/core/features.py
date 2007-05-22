# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

from pida.core.base import BaseConfig

from pida.core.plugins import Registry

class FeaturesConfig(BaseConfig):

    def create(self):
        self._features = Registry()
        self._featurenames = []
        self._foreign_feature_objects = {}
        self.create_features()

    def create_features(self):
        """Create the features here"""

    def create_feature(self, name):
        self._featurenames.append(name)

    def list_features(self):
        return self._featurenames

    def subscribe_foreign_features(self):
        """Subscribe to features here"""

    def unsubscribe_foreign_features(self):
        for (servicename, featurename), feature_objects in self._foreign_feature_objects.items():
            for feature_object in feature_objects:
                self.svc.unsubscribe_foreign_feature(servicename, feature_object)
            del self._foreign_feature_objects[(servicename, featurename)]

    def has_foreign_feature(self, servicename, featurename):
        for (service, feature), feature_object in self._foreign_feature_objects.items():
            if servicename == service and featurename == feature:
                return True
        return False

    def subscribe_foreign_feature(self, servicename, featurename, instance):
        feature_object = self.svc.subscribe_foreign_feature(servicename, featurename, instance)
        self._foreign_feature_objects.setdefault((servicename, featurename), []).append(feature_object)

    def subscribe_feature(self, featurename, instance):
        return self._features.register_plugin(
            instance=instance,
            features=(featurename,)
        )

    def unsubscribe_feature(self, feature_object):
        self._features.unregister(feature_object)

    def get_feature_providers(self, featurename):
        return self._features.get_features(featurename)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
