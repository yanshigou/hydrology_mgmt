// polyfill Array Functions

(function () {

  // findIndex
  if (!Array.prototype.findIndex) {

    function findIndex(predicate, context) {

      if (typeof predicate !== 'function') {
        throw new TypeError('Array#findIndex: predicate must be a function')
      }

      for (var index = 0; index < this.length; index++) {
        if (predicate.call(context, this[index], index, this)) {
          return index
        }
      }

      return -1
    }

    if (Object.defineProperty) {

      Object.defineProperty(Array.prototype, 'findIndex', {
        value: findIndex
      })

    } else {

      Array.prototype.findIndex = findIndex
    }
  }

  // forEach
  if (!Array.prototype.forEach) {
    function forEach(predicate, context) {

      if (typeof predicate !== 'function') {
        throw new TypeError('Array#forEach: predicate must be a function')
      }

      for (var index = 0; index < this.length; index++) {
        predicate.call(context, this[index], index, this)
      }
    }

    if (Object.defineProperty) {

      Object.defineProperty(Array.prototype, 'forEach', {
        value: forEach
      })

    } else {

      Array.prototype.forEach = forEach
    }
  }

})();
