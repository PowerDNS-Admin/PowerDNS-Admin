# jquery-notific8

Notific8 is a notification plug-in inspired by the notifications introduced in Windows 8 with some web ready restyling and customizations. Notific8 has built in themes and is easy to create new themes for. The plug-in was born from a want for a simply designed yet modern and stylish notification system. The plug-in is also designed to scale based on the page's font-size setting (it was designed for the default of 100%/16px as the default).

## Demo page

An interactive demo page can be found here http://willsteinmetz.net/jquery/notific8

## Features

* Notifications slide in and out from the upper right corner of the page
* Configurable life span of the notification
* Option to display a heading
* Theme options (see CSS for built in themes)
* Ability to make the notification sticky
* Ability to set up custom settings for reuse without having to type them over and over
* Ability to set which corner the notifications are shown in
* Ability to set the z-index
    * Can be set via config/configure or the zindex function

## Usage

    // basic
    $.notific8('My notification message goes here.');
    // with a life set
    $.notific8('My notification message has a life span.', {life: 5000});
    // with a heading
    $.notific8('My notification has a heading line.', {heading: 'Notification Heading'});
    // with a theme
    $.notific8('My notification has a theme.', {theme: 'amethyst'});
    // make the notification sticky
    $.notific8('My notification is sticky.', {sticky: true});
    // change whether to notification is at the top or bottom
    $.notific8('My notification is at the bottom.', {horizontalEdge: 'bottom'});
    // change whether to notification is on the left or right
    $.notific8('My notification is on the left.', {verticalEdge: 'left'});
    // set the z-index
    $.notific8('My notification has a z-index of 1500.', {zindex: 1500});
    // all options set
    $.notific8('My notification with all options.', {
      life: 5000,
      heading: 'Notification Heading',
      theme: 'amethyst',
      sticky: true,
      horizontalEdge: 'bottom',
      verticalEdge: 'left',
      zindex: 1500
    });
    
    // set up your own default settings to save time and typing later
    // NOTE this is not required
    $.notific8('configure', {
      life: 5000,
      theme: 'ruby',
      sticky: true,
      horizontalEdge: 'bottom',
      verticalEdge: 'left',
      zindex: 1500
    });
    
    // set the zindex
    $.notific8('zindex', 1500);


## Options

* life: number of milliseconds that the notification will be visible (default: 10000)
* heading: short heading for the notification
* theme: string for the theme (default: 'teal')
    * Custom themes should be named .jquery-notific8-notification.[theme name] in your stylesheet - see note below about custom themes
* sticky: boolean for whether or not the notification should stick
    * If sticky is set to true, life will be ignored if it is also set
* horizontalEdge: string value for top or bottom of the page (default: 'top')
    * only accepts values 'top' and 'bottom'
* verticalEdge: string value for left or right of the page (default: 'right')
    * only accepts values 'left' and 'right'
* zindex: integer value for the z-index (default: 1100)
    * this must be set before calling notific8 to create a notification via either config/configure or zindex

All of these settings are available to be configured. The configure function is used if you have specific settings such as theme and life that you want every notification to share. By configuring these settings, they become the new defaults and you don't have to type them for every notification. The configure function can be called multiple times.

## Custom themes
As of notific8 version 0.9.0, the plug-in's CSS is coded in SASS (SCSS format) and Compass. To create a custom theme, open the jquery.notific8.scss file, copy and paste the template line, uncomment your pasted line, and replace the variables with your own values. Be sure to recompile your SASS file to CSS to use the new theme. The goal is to only make updates to the _notific8.scss file so that updates will not wipe out your custom themes.

If you are using SASS for the rest of your project, you can include the _notific8.scss file in your project's main SCSS file to create your custom themes in there.

## Browser support

Currently supported and testing:
* Chrome
* Firefox
* Safari (Mac only)
* IE 9+

Future support and testing
* Opera (will start after their transition to webkit)

### Browser version support

As a rule of thumb, only the most recent plus one version older of a browser is supported unless marked otherwise. While it may work in IE8, notific8 will not be tested or officially supported in legacy browsers such as versions of IE older than 9.

## Future plans

* Ability to set an icon for the notification
