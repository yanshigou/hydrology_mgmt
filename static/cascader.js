/**
 * Doc: https:/github.com/shixianqin/cascader
 */

(function (root, factory) {
  if (typeof exports === "object" && typeof module === "object")
    module.exports = factory();
  else if (typeof define === "function" && define.amd) define([], factory);
  else if (typeof exports === "object") exports.Cascader = factory();
  else root.Cascader = factory();
})(this, function () {

  function addEvent(element, type, handler) {
    if (element.addEventListener) {
      element.addEventListener(type, handler, false);
    } else {
      var _handler = handler;
      element.attachEvent(
        "on" + type,
        (handler = function () {
          _handler.call(element, window.event);
        })
      );
    }
    return handler;
  }

  function getChildren(list, index) {
    return (list[index] || {}).children || [];
  }

  function findItem(list, value) {
    var index = -1;

    if (value) {
      value = new RegExp(value);
      index = list.findIndex(function (item) {
        return value.test(item.label) || value.test(item.value);
      });
    }

    return {
      index: index,
      children: getChildren(list, index)
    };
  }

  function elementsToArray(elements) {
    var index = 0,
      array = [];

    for (index; index < elements.length; index++) {
      array.push(elements[index]);
    }

    return array;
  }

  function getElements(elements) {
    return elements instanceof Array
      ? elements
      : elements.nodeType === 1
        ? [elements]
        : elementsToArray(elements);
  }

  function createList(element, list, index, placeholder) {
    element.length = 0;
    element.__datalist__ = list;
    placeholder = [{label: placeholder || "\u8BF7\u9009\u62E9"}];

    placeholder.concat(list).forEach(function (item) {
      element.add(new Option(item.label, item.value));
    });

    element.selectedIndex = index + 1;
  }

  function bindChange(element, elements, placeholder) {
    addEvent(element, "change", function () {
      var list = getChildren(this.__datalist__, this.selectedIndex - 1);
      elements.forEach(function (elem, index) {
        createList(elem, list, -1, placeholder[index]);
        list = [];
      });
    });
  }

  function Cascader(options) {
    var initValue = options.initValue || [],
      elements = this.elements = getElements(options.elements),
      placeholder = this.placeholder = (options.placeholder || []);

    this.data = options.data;

    this.setValue(initValue);

    elements.forEach(function (element, index) {
      if (++index < elements.length) {
        bindChange(
          element,
          elements.slice(index),
          placeholder.slice(index)
        );
      }
    });
  }

  Cascader.prototype.setData = function (data) {
    this.data = data;
    this.setValue([]);
  };

  Cascader.prototype.setValue = function (value) {
    var placeholder = this.placeholder,
      list = this.data;

    this.elements.forEach(function (element, level) {
      var item = findItem(list, value[level]);
      createList(element, list, item.index, placeholder[level]);
      list = item.children;
    });
  };

  Cascader.prototype.getValue = function () {
    var values = [], labels = [], indexs = [];

    this.elements.forEach(function (element) {
      var index = element.selectedIndex - 1,
        item = element.__datalist__[index] || {};

      indexs.push(index);
      values.push(item.value);
      labels.push(item.label);
    });

    return {
      value: values,
      label: labels,
      index: indexs
    };
  };

  return Cascader;
});
