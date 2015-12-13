Bootstrap Context Menu
======================

A context menu extension of Bootstrap made for everyone's convenience.

See a [demo page] [id].
[id]:http://sydcanem.github.io/bootstrap-contextmenu/

Installation
------------

`bower install bootstrap-contextmenu`

Note: Requires bootstrap.css

Usage
-----

### Via data attributes

Add `data-toggle="context"` to any element that needs a custom context menu and via CSS set `position: relative` to the element.

Point `data-target` attribute to your custom context menu.

`<div class="context" data-toggle="context" data-target="#context-menu"></div>`

### Via Javascript

Call the context menu via JavaScript:

```js
$('.context').contextmenu({
  target:'#context-menu', 
  before: function(e,context) {
    // execute code before context menu if shown
  },
  onItem: function(context,e) {
    // execute on menu item selection
  }
})
```

### Options

`target` - is the equivalent of the `data-target` attribute. It identifies the html of the menu that will be displayed. 

`before` - is a function that is called before the context menu is displayed. If this function returns false, the context menu will not be displayed. It is passed two parameters,

  - `e` - the original event. (You can do an `e.preventDefault()` to cancel the browser event). 
  - `context` - the DOM element where right click occured.

`onItem` - is a function that is called when a menu item is clicked. Useful when you want to execute a specific function when an item is clicked. It is passed two parameters,

  - `context` - the DOM element where right click occured.
  - `e` - the click event of the menu item, $(e.target) is the item element.

`scopes` - DOM selector for dynamically added context elements. See [issue](https://github.com/sydcanem/bootstrap-contextmenu/issues/56).

### Events

All events are fired at the context's menu. Check out `dropdown` plugin for
a complete description of events.

- `show.bs.context` - This event fires immediately when the menu is opened. 
- `shown.bs.context` - This event is fired when the dropdown has been made visible to the user. 
- `hide.bs.context` - This event is fired immediately when the hide instance method has been called. 
- `hidden.bs.context` - This event is fired when the dropdown has finished being hidden from the user (will wait for CSS transitions, to complete).
  
Sample

```js
$('#myMenu').on('show.bs.context',function () {
  // do something...
});
```

Example
-------

Activate and specify selector for context menu

```js
$('#main').contextmenu({'target':'#context-menu'});
```

Activate within a div, but not on spans

```js
$('#main').contextmenu({
  target: '#context-menu2',
  before: function (e, element, target) {
      e.preventDefault();
      if (e.target.tagName == 'SPAN') {
          e.preventDefault();
          this.closemenu();
          return false;
      }
      return true;
  }
});
```

Modify the menu dynamically

```js
$('#main').contextmenu({
  target: "#myMenu",
  before: function(e) { 
    this.getMenu().find("li").eq(2).find('a').html("This was dynamically changed");
  }
});
```

Show menu name on selection

```js
$('#main').contextmenu({
  onItem: function(context, e) {
    alert($(e.target).text());
  }
});
```

### Nice to have features:

 - Close and open animations
 - Keyboard shortcuts for menus

### License
MIT
