# -*- coding: utf-8 -*-
"""
This is the Layers module. There are five layers in a Carousel model:

* Data
* Formulas
* Calculations
* Outputs
* Simulations

Layers are used to assemble the model. For example, the data layer assembles
all of the :ref:`data-sources`, calling the :ref:`data-readers` and putting all
of the data (and meta) into the
:class:`~carousel.core.data_sources.DataRegistry`.

In general all model layers have add, open and
:meth:`~carousel.core.layers.Layer.load` methods. The add method adds
a particular format such as a
:class:`~carousel.core.data_sources.DataSource`. The open method gets
data from a file in the format that was added. The
:meth:`~carousel.core.layers.Layer.load` method loads the layer into
the model. The :meth:`~carousel.core.layers.Layer.load` method must
be implemented in each subclass of
:class:`~carousel.core.layers.Layer` or
:exc:`~exceptions.NotImplementedError` is raised.
"""

import importlib
import os
from carousel.core import Registry
from carousel.core.simulations import SimRegistry
from carousel.core.data_sources import DataRegistry
from carousel.core.formulas import FormulaRegistry
from carousel.core.calculations import CalcRegistry
from carousel.core.outputs import OutputRegistry


class Layer(object):
    """
    A layer in the model.

    :param layer_data: Dictionary of model data specific to this layer.
    :type layer_data: dict
    """
    reg_cls = NotImplemented  #: registry class

    def __init__(self, sources=None):
        #: dictionary of layer sources
        self.layer = sources
        #: dictionary of layer source classes added to the layer
        self.sources = {}
        #: dictionary of source class instances added to the layer
        self.objects = {}
        #: registry of items contained in this layer
        self.reg = self.reg_cls()

    def add(self, src_cls, module, package=None):
        """
        Add layer class to model. This method may be overloaded by layer.

        :param src_cls: layer class to add, should not start with underscores
        :type src_cls: str
        :param module: Python module that contains layer class
        :type module: str
        :param package: optional package containing module with layer class
        :type package: str
        :raises: :exc:`~exceptions.NotImplementedError`
        """
        # import module containing the layer class
        mod = importlib.import_module(module, package)
        # get layer class definition from the module
        self.sources[src_cls] = getattr(mod, src_cls)

    def load(self, relpath=None):
        """
        Load the layer from the model data. This method must be implemented by
        each layer.

        :param relpath: alternate path if specified path is missing or ``None``
        :raises: :exc:`~exceptions.NotImplementedError`
        """
        raise NotImplementedError('load')

    def delete(self, src_cls):
        """
        Delete layer source class from layer.
        :param src_cls: layer source class to delete.
        :raises: :exc:`~exceptions.NotImplementedError`
        """
        raise NotImplementedError('delete')

    def edit(self, src_cls, value):
        """
        Edit layer source class with value.

        :param src_cls: layer source class to edit
        :type src_cls: str
        :param value: new value of layer source class
        :raises: :exc:`~exceptions.NotImplementedError`
        """
        raise NotImplementedError('delete')


class Data(Layer):
    """
    The Data layer of the model.

    :param data: Dictionary of model data specific to the data layer.
    :type data: :class:`~carousel.core.data_sources.DataRegistry`

    The :attr:`~Layer.layer` attribute is a dictionary of data sources names
    as keys of dictionaries for each data source with the module and optionally
    the package containing the module, the filename, which can be ``None``,
    containing specific data for the data source and an optional path to the
    data file. If the path is ``None``, then the default path for data internal
    to Carousel is used. External data files should specify the path.
    """
    reg_cls = DataRegistry  #: data layer registry

    def add(self, data_source, module, package=None):
        """
        Add data_source to model. Tries to import module, then looks for data
        source class definition.

        :param data_source: Name of data source to add.
        :type data_source: str
        :param module: Module in which data source resides. Can be absolute or
            relative. See :func:`importlib.import_module`
        :type module: str
        :param package: Optional, but must be used if module is relative.
        :type package: str

        .. seealso::
            :func:`importlib.import_module`
        """
        super(Data, self).add(data_source, module, package)
        # only update layer info if it is missing!
        if data_source not in self.layer:
            # copy data source parameters to :attr:`Layer.layer`
            self.layer[data_source] = {'module': module, 'package': package}
        # add a place holder for the data source object when it's constructed
        self.objects[data_source] = None

    def open(self, data_source, filename, path=None, rel_path=None):
        """
        Open filename to get data for data_source.

        :param data_source: Data source for which the file contains data.
        :type data_source: str
        :param filename: Name of the file which contains data for the data
            source.
        :type filename: str
        :param path: Path of file containting data. [../data]
        :type path: str
        :param rel_path: relative path to model file
        """
        # default path for data is in ../data
        if not path:
            path = rel_path
        else:
            path = os.path.join(rel_path, path)
        # only update layer info if it is missing!
        if data_source not in self.layer:
            # update path and filename to this layer of the model
            self.layer[data_source] = {'path': path, 'filename': filename}
        # filename can be a list or a string, concatenate list with os.pathsep
        # and append the full path to strings.
        if isinstance(filename, basestring):
            filename = os.path.join(path, filename)
        else:
            file_list = [os.path.join(path, f) for f in filename]
            filename = os.path.pathsep.join(file_list)
        # call constructor of data source with filename argument
        self.objects[data_source] = self.sources[data_source](filename)
        # register data and uncertainty in registry
        data_src_obj = self.objects[data_source]
        meta = [getattr(data_src_obj, m) for m in self.reg._meta_names]
        self.reg.register(data_src_obj.data, *meta)

    def load(self, rel_path=None):
        """
        Add data_sources to layer and open files with data for the data_source.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))
            if v.get('filename'):
                self.open(k, v['filename'], v.get('path'), rel_path)

    def edit(self, data_src, value):
        """
        Edit data layer.

        :param data_src: Name of :class:`DataSource` to edit.
        :type data_src: str
        :param value: Values to edit.
        :type value: dict
        """
        # check if opening file
        if 'filename' in value:
            items = [k for k, v in self.reg.data_source.iteritems() if
                     v == data_src]
            self.reg.unregister(items)  # remove items from Registry
            # open file and register new data
            self.open(data_src, value['filename'], value.get('path'))
            self.layer[data_src].update(value)  # update layer with new items

    def delete(self, data_src):
        """
        Delete data sources.
        """
        items = self.objects[data_src].data.keys()  # items to edit
        self.reg.unregister(items)  # remove items from Registry
        self.layer.pop(data_src)  # remove data source from layer
        self.objects.pop(data_src)  # remove data_source object
        self.sources.pop(data_src)  # remove data_source object


class Formulas(Layer):
    """
    Layer containing formulas.
    """
    reg_cls = FormulaRegistry  #: formula layer registry

    def add(self, formula, module, package=None):
        """
        Import module (from package) with formulas, import formulas and add
        them to formula registry.

        :param formula: Name of the formula source to add/open.
        :param module: Module containing formula source.
        :param package: [Optional] Package of formula source module.

        .. seealso::
            :func:`importlib.import_module`
        """
        super(Formulas, self).add(formula, module, package)
        # only update layer info if it is missing!
        if formula not in self.layer:
            # copy formula source parameters to :attr:`Layer.layer`
            self.layer[formula] = {'module': module, 'package': package}
        self.objects[formula] = self.sources[formula]()
        # register formula and linearity in registry
        formula_src_obj = self.objects[formula]
        meta = [getattr(formula_src_obj, m) for m in self.reg._meta_names]
        self.reg.register(formula_src_obj.formulas, *meta)

    def open(self, formula, module, package=None):
        self.add(formula, module, package=package)

    def load(self, _=None):
        """
        Add formulas to layer.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))


class Calculations(Layer):
    """
    Layer containing formulas.
    """
    reg_cls = CalcRegistry  #: calculations layer registry

    def add(self, calc, module, package=None):
        """
        Add calc to layer.
        """
        super(Calculations, self).add(calc, module, package)
        # instantiate the calc object
        self.objects[calc] = self.sources[calc]()
        # register calc and dependencies in registry
        calc_src_obj = self.objects[calc]
        meta = [{str(calc): getattr(calc_src_obj, m)} for m in
                self.reg._meta_names]
        self.reg.register({calc: calc_src_obj}, *meta)

    def open(self, calc, module, package=None):
        self.add(calc, module, package=package)

    def load(self, _=None):
        """
        Add calcs to layer.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))


class Outputs(Layer):
    """
    Layer containing output sources.
    """
    reg_cls = OutputRegistry  #: output layer registry

    def add(self, output, module, package=None):
        """
        Add output to
        """
        super(Outputs, self).add(output, module, package)
        # instantiate the output object
        self.objects[output] = self.sources[output]()
        # register outputs and meta-data in registry
        out_src_obj = self.objects[output]
        meta = [getattr(out_src_obj, m) for m in self.reg._meta_names]
        self.reg.register(out_src_obj.outputs, *meta)

    def open(self, output, module, package=None):
        self.add(output, module, package=package)

    def load(self, _=None):
        """
        Add output_source to layer.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))


class Simulations(Layer):
    """
    Layer containing simulation sources.
    """
    reg_cls = SimRegistry  #: simulation layer registry

    def add(self, sim, module, package=None):
        """
        Add simulation to layer.
        """
        super(Simulations, self).add(sim, module, package)

    def open(self, sim, filename, path=None, rel_path=None):
        # default path for data is in ../simulations
        if not path:
            path = rel_path
        else:
            path = os.path.join(rel_path, path)
        filename = os.path.join(path, filename)
        # call constructor of sim source with filename argument
        self.objects[sim] = self.sources[sim](filename)
        # register simulations in registry, the only reason to register an item
        # is make sure it doesn't overwrite other items
        sim_src_obj = self.objects[sim]
        meta = [{str(sim): getattr(sim_src_obj, m)} for m in
                self.reg._meta_names]
        self.reg.register({sim: sim_src_obj}, *meta)

    def load(self, rel_path=None):
        """
        Add sim_src to layer.
        """
        for k, v in self.layer.iteritems():
            self.add(k, v['module'], v.get('package'))
            self.open(k, v['filename'], v.get('path'), rel_path)