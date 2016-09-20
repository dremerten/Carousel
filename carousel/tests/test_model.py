"""
test model
"""


from nose.tools import ok_
from carousel.core.models import Model, BasicModel
from carousel.tests import PROJ_PATH, pvpower_models, logging
import os

LOGGER = logging.getLogger(__name__)
MODELFILE = 'sandia_performance_model-Tuscon.json'


def test_carousel_model():
    """
    Test Model instantiation.
    """

    model_test_file = os.path.join(PROJ_PATH, 'models', MODELFILE)
    carousel_model_test1 = pvpower_models.SAPM(model_test_file)
    ok_(isinstance(carousel_model_test1, Model))

    carousel_model_test2 = PVPowerSAPM2()
    ok_(isinstance(carousel_model_test2, Model))

    carousel_model_test3 = PVPowerSAPM3()
    ok_(isinstance(carousel_model_test3, Model))


class PVPowerSAPM1(Model):
    modelpath = PROJ_PATH
    modelfile = MODELFILE
    layers_mod = '.layers'
    layers_pkg = 'carousel.core'
    layer_cls_names = {'data': 'Data', 'calculations': 'Calculations',
                       'formulas': 'Formulas', 'outputs': 'Outputs',
                       'simulations': 'Simulations'}
    get_state = BasicModel.get_state
    command = BasicModel.command


class PVPowerSAPM2(Model):
    modelpath = PROJ_PATH
    layers_mod = '.layers'
    layers_pkg = 'carousel.core'
    layer_cls_names = {'data': 'Data', 'calculations': 'Calculations',
                       'formulas': 'Formulas', 'outputs': 'Outputs',
                       'simulations': 'Simulations'}
    outputs = {
        "PVPowerOutputs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "PerformanceOutputs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "IrradianceOutputs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        }
    }
    formulas = {
        "UtilityFormulas": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "PerformanceFormulas": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "IrradianceFormulas": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        }
    }
    data = {
        "PVPowerData": {
            "module": ".sandia_performance_model",
            "package": "pvpower",
            "filename": "Tuscon.json",
            "path": None
        }
    }
    calculations = {
        "UtilityCalcs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "PerformanceCalcs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        },
        "IrradianceCalcs": {
            "module": ".sandia_performance_model",
            "package": "pvpower"
        }
    }
    simulations = {
        "Standalone": {
            "module": ".sandia_performance_model",
            "package": "pvpower",
            "filename": "Tuscon.json",
            "path": "Standalone"
        }
    }
    get_state = BasicModel.get_state
    command = BasicModel.command


class PVPowerSAPM3(Model):
    outputs = [
        pvpower_models.PVPowerOutputs,
        pvpower_models.PerformanceOutputs,
        pvpower_models.IrradianceOutputs
    ]
    formulas = [
        pvpower_models.UtilityFormulas,
        pvpower_models.PerformanceFormulas,
        pvpower_models.IrradianceFormulas
    ]
    data = [pvpower_models.PVPowerData("Tuscon.json")]
    calculations = [
        pvpower_models.UtilityCalcs,
        pvpower_models.PerformanceCalcs,
        pvpower_models.IrradianceCalcs
    ]
    simulations = [
        pvpower_models.Standalone(os.path.join("Standalone", "Tuscon.json"))
    ]
    get_state = BasicModel.get_state
    command = BasicModel.command


if __name__ == '__main__':
    m1 = PVPowerSAPM1()
    m2 = PVPowerSAPM2()
