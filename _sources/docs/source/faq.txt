**************************
Frequently Asked Questions
**************************

Why wxPython3.0 and not wxPython2.8?
====================================

The ToolBar class of version 2.8 misses some important methods like ``GetToolByPos`` and ``AddStretchableSpace``.

More importantly, the layout gets all messed up:

.. image:: ../_static/wx30_vs_wx28.jpg