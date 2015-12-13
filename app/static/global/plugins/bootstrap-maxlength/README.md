# [Bootstrap MaxLength](http://mimo84.github.com/bootstrap-maxlength/) [![Build Status](https://travis-ci.org/mimo84/bootstrap-maxlength.png?branch=master)](https://travis-ci.org/mimo84/bootstrap-maxlength) [![Total views](https://sourcegraph.com/api/repos/github.com/mimo84/bootstrap-maxlength/counters/views.png)](https://sourcegraph.com/github.com/mimo84/bootstrap-maxlength)


This plugin integrates by default with Twitter bootstrap using badges to display the maximum length of the field where the user is inserting text.
This plugin uses the HTML5 attribute "maxlength" to work.


The indicator badge show up on focusing on the element, and disappear when the focus is lost.

## Configurable options

 * **alwaysShow**: if true the threshold will be ignored and the remaining length indication will be always showing up while typing or on focus on the input. Default: false.
 * **threshold**: this is a number indicating how many chars are left to start displaying the indications. Default: 10.
 * **warningClass**: it's the class of the element with the indicator. By default is the bootstrap "label label-success" but can be changed to anything you'd like.
 * **limitReachedClass**: it's the class the element gets when the limit is reached. Default is "label label-important label-danger" (to support Bootstrap 2 and 3).
 * **separator**: represents the separator between the number of typed chars and total number of available chars. Default is "/".
 * **preText**: is a string of text that can be outputted in front of the indicator. preText is empty by default.
 * **postText**: is a string outputted after the indicator. postText is empty by default.
 * **showMaxLength**: if false, will display just the number of typed characters, e.g. will not display the max length. Default: true.
 * **showCharsTyped**: if false, will display just the remaining length, e.g. will display remaining lenght instead of number of typed characters. Default: true.
 * **placement**: is a string, define where to output the counter. Possible values are: **bottom** ( *default option* ), **left**, **top**, **right**, **bottom-right**, **top-right**, **top-left**, **bottom-left** and **centered-right**.
 * **message**: an alternative way to provide the message text, i.e. 'You have typed %charsTyped% chars, %charsRemaining% of %charsTotal% remaining'. %charsTyped%, %charsRemaining% and %charsTotal% will be replaced by the actual values. This overrides the options separator, preText, postText and showMaxLength.
 * **utf8**: if true the input will count using utf8 bytesize/encoding.  For example: the '£' character is counted as two characters.
 * **twoCharLinebreak**: count linebreak as 2 characters to match IE/Chrome textarea validation.
 * **customMaxAttribute**: allows a custom maxlength attribute to allow exceeding maxlength.  'overmax' class gets added when exceeded to allow user to implement form validation.

## Examples

Basic implementation:

    $('input[maxlength]').maxlength();

Change the threshold value:

    $('input.className').maxlength({
        threshold: 20
    });

An example with some of the configurable options:

    $('input.className').maxlength({
        alwaysShow: true,
        threshold: 10,
        warningClass: "label label-info",
        limitReachedClass: "label label-warning",
        placement: 'top',
        preText: 'used ',
        separator: ' of ',
        postText: ' chars.'
    });

The same example using the message option:

    $('input.className').maxlength({
        alwaysShow: true,
        threshold: 10,
        warningClass: "label label-info",
        limitReachedClass: "label label-warning",
        placement: 'top',
        message: 'used %charsTyped% of %charsTotal% chars.'
    });

An example allowing user to enter over max characters.
	Sample HTML element:
```html
		<textarea class="form-control" id="xyz" name="xyz" maxlength="10"></textarea>
```

	// Setup maxlength
	$('.form-control').maxlength({
		alwaysShow: true,
		validate: false,
		allowOverMax: true
	});

	// validate form before submit
	$('form').on('submit', function (e) {
		$('.form-control').each(
			function () {
				if ($(this).hasClass('overmax')) {
					alert('prevent submit here');
					e.preventDefault();
					return false;
				}
			}
		);
	});

## Changelog

### 1.5.7
*   Fixed issue with bower

### 1.5.6
*   Added over maxlength functionality with customMaxAttribute
*   Added twoCharLinebreak option

### 1.5.5
*   Implemented input event rather than keydown to improve usability
*   Fixed jshint, jscs errors

### 1.5.4

*   When an input with associated maxlength element is removed, maxlength is also removed.

### 1.5.3

*   Fixed #40, error on resize event.

### 1.5.2

*   Fixed #44 (pasted text in can cause it to go over the max length)

### 1.5.1

*   Added self protection of multiple focus events
*   Added back detection of window resizing

### 1.5.0

*   Removed window.resize event
*   Maxlength is created and destroyed each time
*   Fixed Doesn't update the limit after input's maxlength attribute was changed [#31](https://github.com/mimo84/bootstrap-maxlength/issues/31)
*   Added Gruntfile
*   Added qunit unit tests

### 1.4.2

* Fixed issue with counting when the user moves with shift+tab keyboard shortcut.
* Replaced the warningClass limitReachedClass options to use labels rather than badges for Bootstrap 3.0 better compatibility.

### 1.4.1

* Added support for TAB key when the maxlength is reached.
