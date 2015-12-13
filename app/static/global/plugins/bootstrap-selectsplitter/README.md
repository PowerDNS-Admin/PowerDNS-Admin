# bootstrap-selectsplitter

## Presentation

Transforms SELECT containing one or more OPTGROUP in two chained SELECT.

This:

![image1](http://img4.hostingpics.net/pics/927121bootstrapselectsplitterimage1.png)

Becomes this:

![image2](http://img4.hostingpics.net/pics/997752bootstrapselectsplitterimage2.png)

## Demo

See the [online demo](http://jsfiddle.net/ae7fxdyy/).

## How to use

Create a SELECT tag containing one or more OPTGROUP:

```HTML
<select data-selectsplitter-selector>
  <optgroup label="Category 1">
    <option value="1">Choice 1</option>
    <option value="2">Choice 2</option>
    <option value="3">Choice 3</option>
    <option value="4">Choice 4</option>
  </optgroup>
  <optgroup label="Category 2">
    <option value="5">Choice 5</option>
    <option value="6">Choice 6</option>
    <option value="7">Choice 7</option>
    <option value="8">Choice 8</option>
  </optgroup>
  <optgroup label="Category 3">
    <option value="5">Choice 9</option>
    <option value="6">Choice 10</option>
    <option value="7">Choice 11</option>
    <option value="8">Choice 12</option>
  </optgroup>
</select>
```

Add the dependency files (jQuery and Bootstrap 3 CSS):

```HTML
<link rel="stylesheet" href="//maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css">
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.11.2/jquery.min.js"></script>

<script src="bootstrap-selectsplitter.js"></script>
```

Call the plugin:
```JavaScript
$('select[data-selectsplitter-selector]').selectsplitter();
```

## Bower
bower install bootstrap-selectsplitter

##CDN

```HTML
<script src="//cdn.jsdelivr.net/bootstrap.selectsplitter/0.1.0/bootstrap-selectsplitter.min.js"></script>
```

## Copyright and license

Copyright (C) 2015 Xavier Faucon

Licensed under the MIT license. 

