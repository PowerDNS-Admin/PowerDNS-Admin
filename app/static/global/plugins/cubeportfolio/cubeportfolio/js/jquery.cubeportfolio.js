/*!
 * Cube Portfolio - Responsive jQuery Grid Plugin
 *
 * version: 2.1.1 (7 April, 2015)
 * require: jQuery v1.7+
 *
 * Copyright 2013-2015, Mihai Buricea (http://scriptpie.com/cubeportfolio/live-preview/)
 * Licensed under CodeCanyon License (http://codecanyon.net/licenses)
 *
 */

(function($, window, document, undefined) {

    'use strict';

    function CubePortfolio(obj, options, callback) {
        /*jshint validthis: true */
        var t = this;

        if ($.data(obj, 'cubeportfolio')) {
            throw new Error('cubeportfolio is already initialized. Destroy it before initialize again!');
        }

        // attached this instance to obj
        $.data(obj, 'cubeportfolio', t);

        // extend options
        t.options = $.extend({}, $.fn.cubeportfolio.options, options);

        // store the state of the animation used for filters
        t.isAnimating = true;

        // default filter for plugin
        t.defaultFilter = t.options.defaultFilter;

        // registered events (observator & publisher pattern)
        t.registeredEvents = [];

        // skip events (observator & publisher pattern)
        t.skipEvents = [];

        // has wrapper
        t.addedWrapp = false;

        // register callback function
        if ($.isFunction(callback)) {
            t._registerEvent('initFinish', callback, true);
        }

        // js element
        t.obj = obj;

        // jquery element
        t.$obj = $(obj);

        t.$obj.addClass('cbp');

        if (t.$obj.children().first().hasClass('cbp-item')) {
            t.wrapInner(t.obj, 'cbp-wrapper');
            t.addedWrapp = true;
        }

        // jquery wrapper element
        t.$ul = t.$obj.children().addClass('cbp-wrapper');

        // wrap the $ul in a outside wrapper
        t.wrapInner(t.obj, 'cbp-wrapper-outer');

        t.wrapper = t.$obj.children('.cbp-wrapper-outer');

        // wrap .cbp-item-wrap div inside .cbp-item
        t.wrapInner(t.obj.querySelectorAll('.cbp-item'), 'cbp-item-wrapper');

        // store main container width
        t.width = t.$obj.outerWidth();

        // cache the blocks
        t.blocks = t.$ul.children('.cbp-item');

        if (t.blocks.length < 1) {
            return;
        }

        t.blocksObj = t.blocks.map(function(index, el) {
            return t.generateBlock($(el));
        });

        t.blocksOn = t.blocksObj;

        if (t.options.layoutMode === 'grid') {
            // set default filter if is present in url
            t._filterFromUrl();
        }

        if (t.defaultFilter !== '*') {
            t.blocksOn = $.map(t.blocksObj, function(item) {
                if (item.el.is(t.defaultFilter)) {
                    return item;
                }
                item.el.addClass('cbp-item-off');
            });
        }

        // internal plugins. these must run before _load in 2.1.0  to not break the singlePage
        t._plugins = $.map(CubePortfolio.Plugins, function(pluginName) {
            return pluginName(t);
        });

        // wait to load all images and then go further
        t._load(t.$obj, t._display);
    }

    $.extend(CubePortfolio.prototype, {

        generateBlock: function(el) {
            return {
                el: el,
                wrapper: el.children('.cbp-item-wrapper'),

                elClone: null,
                wrapperClone: null,

                widthInitial: el.outerWidth(),
                heightInitial: el.outerHeight(),

                width: null,
                height: null,

                left: null,
                leftNew: null,
                top: null,
                topNew: null,

                elFront: el,
            };
        },

        // http://bit.ly/pure-js-wrap
        wrapInner: function(items, classAttr) {
            var t = this,
                item,
                i,
                div;

            classAttr = classAttr || '';

            items = (items.length) ? items : [items];

            for (i = items.length - 1; i >= 0; i--) {
                item = items[i];

                div = document.createElement('div');

                div.setAttribute('class', classAttr);

                while (item.childNodes.length) {
                    div.appendChild(item.childNodes[0]);
                }

                item.appendChild(div);

            }
        },


        /**
         * Destroy function for all captions
         */
        _captionDestroy: function() {
            var t = this;
            t.$obj.removeClass('cbp-caption-' + t.options.caption);
        },


        /**
         * Add resize event when browser width changes
         */
        resizeEvent: function() {
            var t = this,
                timeout, gridWidth;

            // resize
            $(window).on('resize.cbp', function() {
                clearTimeout(timeout);

                timeout = setTimeout(function() {

                    if (window.innerHeight == screen.height) {
                        // this is fulll screen mode. don't need to trigger a resize
                        return;
                    }

                    if (t.options.gridAdjustment === 'alignCenter') {
                        t.obj.style.maxWidth = '';
                    }

                    gridWidth = t.$obj.outerWidth();

                    if (t.width !== gridWidth) {

                        // update the current width
                        t.width = gridWidth;

                        // make responsive
                        if (t.options.gridAdjustment === 'responsive') {
                            t._responsiveLayout();
                        }

                        // reposition the blocks
                        t._layout();

                        // repositionate the blocks with the best transition available
                        t.positionateItems();

                        // resize main container height
                        t._resizeMainContainer();

                        if (t.options.layoutMode === 'slider') {
                            t._updateSlider();
                        }

                        t._triggerEvent('resizeGrid');
                    }

                    t._triggerEvent('resizeWindow');

                }, 80);
            });

        },


        /**
         * Wait to load all images
         */
        _load: function(obj, callback, args) {
            var t = this,
                imgs,
                imgsLength,
                imgsLoaded = 0;

            args = args || [];

            imgs = obj.find('img:uncached').map(function() {
                return this.src;
            });

            imgsLength = imgs.length;

            if (imgsLength === 0) {
                callback.apply(t, args);
            }

            $.each(imgs, function(i, src) {
                var img = new Image();

                $(img).one('load.cbp error.cbp', function() {
                    $(this).off('load.cbp error.cbp');

                    imgsLoaded++;
                    if (imgsLoaded === imgsLength) {
                        callback.apply(t, args);
                        return false;
                    }

                });

                img.src = src;
            });

        },


        /**
         * Check if filters is present in url
         */
        _filterFromUrl: function() {
            var t = this,
                match = /#cbpf=(.*?)([#|?&]|$)/gi.exec(location.href);

            if (match !== null) {
                t.defaultFilter = match[1];
            }
        },


        /**
         * Show the plugin
         */
        _display: function() {
            var t = this;

            t._triggerEvent('initStartRead');
            t._triggerEvent('initStartWrite');

            t.localColumnWidth = t.blocksObj[0].widthInitial + t.options.gapVertical;

            t.getColumnsType = ($.isArray(t.options.mediaQueries)) ? '_getColumnsBreakpoints' : '_getColumnsAuto';

            // if responsive
            if (t.options.gridAdjustment === 'responsive') {
                t._responsiveLayout();
            } else {
                $.each(t.blocksObj, function(index, item) {
                    item.width = item.widthInitial;
                    item.height = item.heightInitial;
                });
            }

            // create mark-up for layout mode
            t['_' + t.options.layoutMode + 'Markup']();

            // make layout
            t._layout();

            // positionate the blocks
            t.positionateItems();

            // resize main container height
            t._resizeMainContainer();

            t._triggerEvent('initEndRead');
            t._triggerEvent('initEndWrite');

            // if caption is active
            if (t.options.caption) {
                if (!CubePortfolio.Private.modernBrowser) {
                    t.options.caption = 'minimal';
                }

                t.$obj.addClass('cbp-caption-' + t.options.caption);
            }

            // plugin is ready to show and interact
            t.$obj.addClass('cbp-ready');

            t._registerEvent('delayFrame', t.delayFrame);

            //  the reason is to skip this event when you want from a plugin
            t._triggerEvent('delayFrame');

        },

        positionateItems: function() {
            var t = this,
                i,
                item;

            for (i = t.blocksOn.length - 1; i >= 0; i--) {
                item = t.blocksOn[i];

                item.left = item.leftNew;
                item.top = item.topNew;

                item.elFront[0].style.left = item.left + 'px';
                item.elFront[0].style.top = item.top + 'px';

            }

        },

        delayFrame: function() {
            var t = this;

            requestAnimationFrame(function() {
                t.resizeEvent();

                t._triggerEvent('initFinish');

                // animating is now false
                t.isAnimating = false;

                // trigger public event initComplete
                t.$obj.trigger('initComplete.cbp');
            });

        },


        /**
         * Build the layout
         */
        _layout: function() {
            var t = this;

            t['_' + t.options.layoutMode + 'LayoutReset']();

            t['_' + t.options.layoutMode + 'Layout']();

            t.$obj.removeClass(function(index, css) {
                return (css.match(/\bcbp-cols-\d+/gi) || []).join(' ');
            });

            t.$obj.addClass('cbp-cols-' + t.cols);

        },

        // create mark
        _sliderMarkup: function() {
            var t = this;

            t.sliderStopEvents = false;

            t.sliderActive = 0;

            t._registerEvent('updateSliderPosition', function() {
                t.$obj.addClass('cbp-mode-slider');
            }, true);

            t.nav = $('<div/>', {
                'class': 'cbp-nav'
            });

            t.nav.on('click.cbp', '[data-slider-action]', function(e) {
                e.preventDefault();
                e.stopImmediatePropagation();
                e.stopPropagation();

                if (t.sliderStopEvents) {
                    return;
                }

                var el = $(this),
                    action = el.attr('data-slider-action');

                if (t['_' + action + 'Slider']) {
                    t['_' + action + 'Slider'](el);
                }

            });

            if (t.options.showNavigation) {
                t.controls = $('<div/>', {
                    'class': 'cbp-nav-controls'
                });

                t.navPrev = $('<div/>', {
                    'class': 'cbp-nav-prev',
                    'data-slider-action': 'prev'
                }).appendTo(t.controls);

                t.navNext = $('<div/>', {
                    'class': 'cbp-nav-next',
                    'data-slider-action': 'next'
                }).appendTo(t.controls);


                t.controls.appendTo(t.nav);
            }

            if (t.options.showPagination) {
                t.navPagination = $('<div/>', {
                    'class': 'cbp-nav-pagination'
                }).appendTo(t.nav);
            }

            if (t.controls || t.navPagination) {
                t.nav.appendTo(t.$obj);
            }

            t._updateSliderPagination();

            if (t.options.auto) {
                if (t.options.autoPauseOnHover) {
                    t.mouseIsEntered = false;
                    t.$obj.on('mouseenter.cbp', function(e) {
                        t.mouseIsEntered = true;
                        t._stopSliderAuto();
                    }).on('mouseleave.cbp', function(e) {
                        t.mouseIsEntered = false;
                        t._startSliderAuto();
                    });
                }

                t._startSliderAuto();
            }

            if (t.options.drag && CubePortfolio.Private.modernBrowser) {
                t._dragSlider();
            }

        },

        _updateSlider: function() {
            var t = this;

            t._updateSliderPosition();

            t._updateSliderPagination();

        },

        _updateSliderPagination: function() {
            var t = this,
                pages,
                i;

            if (t.options.showPagination) {

                // get number of pages
                pages = Math.ceil(t.blocksOn.length / t.cols);
                t.navPagination.empty();

                for (i = pages - 1; i >= 0; i--) {
                    $('<div/>', {
                        'class': 'cbp-nav-pagination-item',
                        'data-slider-action': 'jumpTo'
                    }).appendTo(t.navPagination);
                }

                t.navPaginationItems = t.navPagination.children();
            }

            // enable disable the nav
            t._enableDisableNavSlider();
        },

        _destroySlider: function() {
            var t = this;

            if (t.options.layoutMode !== 'slider') {
                return;
            }

            t.$obj.off('click.cbp');

            t.$obj.removeClass('cbp-mode-slider');

            if (t.options.showNavigation) {
                t.nav.remove();
            }

            if (t.navPagination) {
                t.navPagination.remove();
            }

        },

        _nextSlider: function(el) {
            var t = this;

            if (t._isEndSlider()) {
                if (t.isRewindNav()) {
                    t.sliderActive = 0;
                } else {
                    return;
                }
            } else {
                if (t.options.scrollByPage) {
                    t.sliderActive = Math.min(t.sliderActive + t.cols, t.blocksOn.length - t.cols);
                } else {
                    t.sliderActive += 1;
                }
            }

            t._goToSlider();
        },

        _prevSlider: function(el) {
            var t = this;

            if (t._isStartSlider()) {
                if (t.isRewindNav()) {
                    t.sliderActive = t.blocksOn.length - t.cols;
                } else {
                    return;
                }
            } else {
                if (t.options.scrollByPage) {
                    t.sliderActive = Math.max(0, t.sliderActive - t.cols);
                } else {
                    t.sliderActive -= 1;
                }
            }

            t._goToSlider();
        },

        _jumpToSlider: function(el) {
            var t = this,
                index = Math.min(el.index() * t.cols, t.blocksOn.length - t.cols);

            if (index === t.sliderActive) {
                return;
            }

            t.sliderActive = index;

            t._goToSlider();
        },

        _jumpDragToSlider: function(pos) {
            var t = this,
                jumpWidth,
                offset,
                condition,
                index,
                dragLeft = (pos > 0) ? true : false;

            if (t.options.scrollByPage) {
                jumpWidth = t.cols * t.localColumnWidth;
                offset = t.cols;
            } else {
                jumpWidth = t.localColumnWidth;
                offset = 1;
            }

            pos = Math.abs(pos);
            index = Math.floor(pos / jumpWidth) * offset;
            if (pos % jumpWidth > 20) {
                index += offset;
            }

            if (dragLeft) { // drag to left
                t.sliderActive = Math.min(t.sliderActive + index, t.blocksOn.length - t.cols);
            } else { // drag to right
                t.sliderActive = Math.max(0, t.sliderActive - index);
            }

            t._goToSlider();
        },

        _isStartSlider: function() {
            return this.sliderActive === 0;
        },

        _isEndSlider: function() {
            var t = this;
            return (t.sliderActive + t.cols) > t.blocksOn.length - 1;
        },

        _goToSlider: function() {
            var t = this;

            // enable disable the nav
            t._enableDisableNavSlider();

            t._updateSliderPosition();

        },

        _startSliderAuto: function() {
            var t = this;

            if (t.isDrag) {
                t._stopSliderAuto();
                return;
            }

            t.timeout = setTimeout(function() {

                // go to next slide
                t._nextSlider();

                // start auto
                t._startSliderAuto();

            }, t.options.autoTimeout);
        },

        _stopSliderAuto: function() {
            clearTimeout(this.timeout);
        },

        _enableDisableNavSlider: function() {
            var t = this,
                page,
                method;

            if (!t.isRewindNav()) {
                method = (t._isStartSlider()) ? 'addClass' : 'removeClass';
                t.navPrev[method]('cbp-nav-stop');

                method = (t._isEndSlider()) ? 'addClass' : 'removeClass';
                t.navNext[method]('cbp-nav-stop');
            }

            if (t.options.showPagination) {

                if (t.options.scrollByPage) {
                    page = Math.ceil(t.sliderActive / t.cols);
                } else {
                    if (t._isEndSlider()) {
                        page = t.navPaginationItems.length - 1;
                    } else {
                        page = Math.floor(t.sliderActive / t.cols);
                    }
                }

                // add class active on pagination's items
                t.navPaginationItems.removeClass('cbp-nav-pagination-active')
                    .eq(page)
                    .addClass('cbp-nav-pagination-active');
            }

        },

        /**
         * If slider loop is enabled don't add classes to `next` and `prev` buttons
         */
        isRewindNav: function() {
            var t = this;

            if (!t.options.showNavigation) {
                return true;
            }

            if (t.blocksOn.length <= t.cols) {
                return false;
            }

            if (t.options.rewindNav) {
                return true;
            }

            return false;
        },

        sliderItemsLength: function() {
            return this.blocksOn.length <= this.cols;
        },


        /**
         * Arrange the items in a slider layout
         */
        _sliderLayout: function() {
            var t = this;

            $.each(t.blocksOn, function(index, item) {

                var setHeight;

                // update the values with the new ones
                item.leftNew = Math.round(t.localColumnWidth * index);
                item.topNew = 0;

                setHeight = item.height + t.options.gapHorizontal;
                t.colVert.push(setHeight);

            });

            t.sliderColVert = t.colVert.slice(t.sliderActive, t.sliderActive + t.cols);

            t.ulWidth = t.localColumnWidth * t.blocksOn.length - t.options.gapVertical;
            t.$ul.width(t.ulWidth);

        },

        _updateSliderPosition: function() {
            var t = this,
                value = -t.sliderActive * t.localColumnWidth;

            t._triggerEvent('updateSliderPosition');

            if (CubePortfolio.Private.modernBrowser) {
                t.$ul[0].style[CubePortfolio.Private.transform] = 'translate3d(' + value + 'px, 0px, 0)';
            } else {
                t.$ul[0].style.left = value + 'px';
            }

            t.sliderColVert = t.colVert.slice(t.sliderActive, t.sliderActive + t.cols);
            t._resizeMainContainer();

        },

        _dragSlider: function() {
            var t = this,
                $document = $(document),
                posInitial,
                pos,
                target,
                ulPosition,
                ulMaxWidth,
                isAnimating = false,
                events = {},
                isTouch = false,
                touchStartEvent,
                isHover = false;

            t.isDrag = false;

            if (('ontouchstart' in window) ||
                (navigator.maxTouchPoints > 0) ||
                (navigator.msMaxTouchPoints > 0)) {

                events = {
                    start: 'touchstart.cbp',
                    move: 'touchmove.cbp',
                    end: 'touchend.cbp'
                };

                isTouch = true;
            } else {
                events = {
                    start: 'mousedown.cbp',
                    move: 'mousemove.cbp',
                    end: 'mouseup.cbp'
                };
            }

            function dragStart(e) {
                if (t.sliderItemsLength()) {
                    return;
                }

                if (!isTouch) {
                    e.preventDefault();
                } else {
                    touchStartEvent = e;
                }

                if (t.options.auto) {
                    t._stopSliderAuto();
                }

                if (isAnimating) {
                    $(target).one('click.cbp', function() {
                        return false;
                    });
                    return;
                }

                target = $(e.target);
                posInitial = pointerEventToXY(e).x;
                pos = 0;
                ulPosition = -t.sliderActive * t.localColumnWidth;
                ulMaxWidth = t.localColumnWidth * (t.blocksOn.length - t.cols);

                $document.on(events.move, dragMove);
                $document.on(events.end, dragEnd);

                t.$obj.addClass('cbp-mode-slider-dragStart');
            }

            function dragEnd(e) {
                t.$obj.removeClass('cbp-mode-slider-dragStart');

                // put the state to animate
                isAnimating = true;

                if (pos !== 0) {
                    target.one('click.cbp', function() {
                        return false;
                    });

                    t._jumpDragToSlider(pos);

                    t.$ul.one(CubePortfolio.Private.transitionend, afterDragEnd);
                } else {
                    afterDragEnd.call(t);
                }

                $document.off(events.move);
                $document.off(events.end);
            }

            function dragMove(e) {
                pos = posInitial - pointerEventToXY(e).x;

                if (pos > 8 || pos < -8) {
                    e.preventDefault();
                }

                t.isDrag = true;

                var value = ulPosition - pos;

                if (pos < 0 && pos < ulPosition) { // to right
                    value = (ulPosition - pos) / 5;
                } else if (pos > 0 && (ulPosition - pos) < -ulMaxWidth) { // to left
                    value = -ulMaxWidth + (ulMaxWidth + ulPosition - pos) / 5;
                }

                if (CubePortfolio.Private.modernBrowser) {
                    t.$ul[0].style[CubePortfolio.Private.transform] = 'translate3d(' + value + 'px, 0px, 0)';
                } else {
                    t.$ul[0].style.left = value + 'px';
                }

            }

            function afterDragEnd() {
                isAnimating = false;
                t.isDrag = false;

                if (t.options.auto) {

                    if (t.mouseIsEntered) {
                        return;
                    }

                    t._startSliderAuto();

                }
            }

            function pointerEventToXY(e) {

                if (e.originalEvent !== undefined && e.originalEvent.touches !== undefined) {
                    e = e.originalEvent.touches[0];
                }

                return {
                    x: e.pageX,
                    y: e.pageY
                };
            }

            t.$ul.on(events.start, dragStart);

        },


        /**
         * Reset the slider layout
         */
        _sliderLayoutReset: function() {
            var t = this;
            t.colVert = [];
        },

        // create mark
        _gridMarkup: function() {

        },

        /**
         * Arrange the items in a grid layout
         */
        _gridLayout: function() {
            var t = this;

            $.each(t.blocksOn, function(index, item) {
                var minVert = Math.min.apply(Math, t.colVert),
                    column = 0,
                    setHeight,
                    colsLen,
                    i,
                    len;

                for (i = 0, len = t.colVert.length; i < len; i++) {
                    if (t.colVert[i] === minVert) {
                        column = i;
                        break;
                    }
                }

                // update the values with the new ones
                item.leftNew = Math.round(t.localColumnWidth * column);
                item.topNew = Math.round(minVert);

                setHeight = minVert + item.height + t.options.gapHorizontal;
                colsLen = t.cols + 1 - len;

                for (i = 0; i < colsLen; i++) {
                    t.colVert[column + i] = setHeight;
                }
            });

        },


        /**
         * Reset the grid layout
         */
        _gridLayoutReset: function() {
            var c, t = this;

            // @options gridAdjustment = alignCenter
            if (t.options.gridAdjustment === 'alignCenter') {

                // calculate numbers of columns
                t.cols = Math.max(Math.floor((t.width + t.options.gapVertical) / t.localColumnWidth), 1);

                t.width = t.cols * t.localColumnWidth - t.options.gapVertical;
                t.$obj.css('max-width', t.width);

            } else {

                // calculate numbers of columns
                t.cols = Math.max(Math.floor((t.width + t.options.gapVertical) / t.localColumnWidth), 1);

            }

            t.colVert = [];
            c = t.cols;

            while (c--) {
                t.colVert.push(0);
            }
        },

        /**
         * Make this plugin responsive
         */
        _responsiveLayout: function() {
            var t = this,
                widthWithoutGap,
                itemWidth;

            if (!t.columnWidthCache) {
                t.columnWidthCache = t.localColumnWidth;
            } else {
                t.localColumnWidth = t.columnWidthCache;
            }

            // calculate numbers of cols
            t.cols = t[t.getColumnsType]();

            // calculate the with of items without the gaps between them
            widthWithoutGap = t.width - t.options.gapVertical * (t.cols - 1);

            // calculate column with based on widthWithoutGap plus the gap
            t.localColumnWidth = parseInt(widthWithoutGap / t.cols, 10) + t.options.gapVertical;

            itemWidth = (t.localColumnWidth - t.options.gapVertical);

            $.each(t.blocksObj, function(index, item) {
                item.el[0].style.width = itemWidth + 'px';

                if (item.elClone) {
                    item.elClone[0].style.width = itemWidth + 'px';
                }

                item.width = itemWidth;
            });

            $.each(t.blocksObj, function(index, item) {
                item.height = item.el.outerHeight();
            });

        },


        /**
         * Get numbers of columns when t.options.mediaQueries is not an array
         */
        _getColumnsAuto: function() {
            var t = this;
            return Math.max(Math.round(t.width / t.localColumnWidth), 1);
        },

        /**
         * Get numbers of columns where t.options.mediaQueries is an array
         */
        _getColumnsBreakpoints: function() {
            var t = this,
                gridWidth = t.width - t.options.gapVertical,
                cols;

            $.each(t.options.mediaQueries, function(index, val) {

                if (gridWidth >= val.width) {
                    cols = val.cols;
                    return false;
                }

            });

            if (cols === undefined) {
                cols = t.options.mediaQueries[t.options.mediaQueries.length - 1].cols;
            }

            return cols;
        },


        /**
         * Resize main container vertically
         */
        _resizeMainContainer: function() {
            var t = this,
                cols = t.sliderColVert || t.colVert,
                height;

            // set container height for `overflow: hidden` to be applied
            height = Math.max(Math.max.apply(Math, cols) - t.options.gapHorizontal, 0);

            if (height === t.height) {
                return;
            }

            t.obj.style.height = height + 'px';

            // if _resizeMainContainer is called for the first time skip this event trigger
            if (t.height !== undefined) {
                if (CubePortfolio.Private.modernBrowser) {
                    t.$obj.one(CubePortfolio.Private.transitionend, function() {
                        t.$obj.trigger('pluginResize.cbp');
                    });
                } else {
                    t.$obj.trigger('pluginResize.cbp');
                }
            }

            t.height = height;
        },

        _filter: function(filterName) {
            var t = this;

            t.filterDeferred = $.Deferred();

            t._triggerEvent('filterBeforeLayout');

            t.blocksOn = $.map(t.blocksObj, function(item) {
                return (item.el.is(filterName)) ? item : null;
            });

            // call layout
            t._layout();

            // resize main container height
            t._resizeMainContainer();

            // filter call layout
            t.filterLayout(filterName);

            t._triggerEvent('filterAfterLayout', filterName);

            t.filterDeferred.done($.proxy(t.filterFinish, t));
        },


        /**
         *  Default filter layout if nothing overrides
         */
        filterLayout: function(filterName) {
            var t = this,
                i, item;

            for (i = t.blocksObj.length - 1; i >= 0; i--) {
                item = t.blocksObj[i];

                if (item.el.is(filterName)) {
                    item.el[0].style.opacity = 1;
                    item.el.removeClass('cbp-item-off');

                    item.left = item.leftNew;
                    item.top = item.topNew;

                    item.el[0].style.left = item.left + 'px';
                    item.el[0].style.top = item.top + 'px';

                } else {
                    item.el[0].style.opacity = 0;
                    item.el.addClass('cbp-item-off');
                }
            }

            // resolve this deferred because there is no animation here
            t.filterDeferred.resolve();
        },


        /**
         *  Trigger when a filter is finished
         */
        filterFinish: function() {
            var t = this;

            t.isAnimating = false;

            t.$obj.trigger('filterComplete.cbp');
            t._triggerEvent('filterFinish');

        },


        /**
         *  Register event
         */
        _registerEvent: function(name, callbackFunction, oneTime) {
            var t = this;

            if (!t.registeredEvents[name]) {
                t.registeredEvents[name] = [];
            }

            t.registeredEvents[name].push({
                func: callbackFunction,
                oneTime: oneTime || false
            });
        },


        /**
         *  Trigger event
         */
        _triggerEvent: function(name, param) {
            var t = this,
                i, len;

            if (t.skipEvents[name]) {
                delete t.skipEvents[name];
                return;
            }

            if (t.registeredEvents[name]) {
                for (i = 0, len = t.registeredEvents[name].length; i < len; i++) {

                    t.registeredEvents[name][i].func.call(t, param);

                    if (t.registeredEvents[name][i].oneTime) {
                        t.registeredEvents[name].splice(i, 1);
                        // function splice change the t.registeredEvents[name] array
                        // if event is one time you must set the i to the same value
                        // next time and set the length lower
                        i--;
                        len--;
                    }

                }
            }

        },


        /**
         *  Delay trigger event
         */
        _skipNextEvent: function(name) {
            var t = this;
            t.skipEvents[name] = true;
        },

        _addItems: function(items, callback) {
            var t = this;

            items = $(items)
                .filter('.cbp-item')
                .addClass('cbp-loading-fadeIn')
                .css('top', '1000%')
                .wrapInner('<div class="cbp-item-wrapper"></div>');

            t.$obj.addClass('cbp-addItems');

            t._load(items, function() {

                items.appendTo(t.$ul);

                // cache the blocks
                t.blocks = t.$ul.children('.cbp-item');

                items.on(CubePortfolio.Private.animationend, function() {
                    t.$obj.find('.cbp-loading-fadeIn').removeClass('cbp-loading-fadeIn');
                    t.$obj.removeClass('cbp-addItems');
                });

                items.each(function(index, el) {
                    t.blocksObj.push(t.generateBlock($(el)));
                });

                t._triggerEvent('addItemsToDOM', items);

                t.blocksOn = $.map(t.blocksObj, function(item) {

                    if (item.el.is(t.defaultFilter)) {
                        return item;
                    } else {
                        item.el.addClass('cbp-item-off');
                    }

                });

                // make responsive
                if (t.options.gridAdjustment === 'responsive') {
                    t._responsiveLayout();
                }

                t._layout();

                t.positionateItems();

                // resize main container height
                t._resizeMainContainer();

                if (t.options.layoutMode === 'slider') {
                    t._updateSlider();
                }

                // if show count was actived, call show count function again
                if (t.elems) {
                    CubePortfolio.Public.showCounter.call(t.obj, t.elems);
                }

                t.$obj.trigger('appendItemsFinish.cbp');
                if ($.isFunction(callback)) {
                    callback.call(t);
                }

            });

        }

    });


    /**
     * jQuery plugin initializer
     */
    $.fn.cubeportfolio = function(method, options, callback) {

        return this.each(function() {

            if (typeof method === 'object' || !method) {
                return CubePortfolio.Public.init.call(this, method, callback);
            } else if (CubePortfolio.Public[method]) {
                return CubePortfolio.Public[method].call(this, options, callback);
            }

            throw new Error('Method ' + method + ' does not exist on jquery.cubeportfolio.js');

        });

    };

    // Plugin default options
    $.fn.cubeportfolio.options = {

        /**
         *  Layout Mode for this instance
         *  Values: 'grid' or 'slider'
         */
        layoutMode: 'grid',

        /**
         *  Mouse and touch drag support
         *  Option available only for `layoutMode: 'slider'`
         *  Values: true or false
         */
        drag: true,

        /**
         *  Autoplay the slider
         *  Option available only for `layoutMode: 'slider'`
         *  Values: true or false
         */
        auto: false,

        /**
         *  Autoplay interval timeout. Time is set in milisecconds
         *  1000 milliseconds equals 1 second.
         *  Option available only for `layoutMode: 'slider'`
         *  Values: only integers (ex: 1000, 2000, 5000)
         */
        autoTimeout: 5000,

        /**
         *  Stops autoplay when user hover the slider
         *  Option available only for `layoutMode: 'slider'`
         *  Values: true or false
         */
        autoPauseOnHover: true,

        /**
         *  Show `next` and `prev` buttons for slider
         *  Option available only for `layoutMode: 'slider'`
         *  Values: true or false
         */
        showNavigation: true,

        /**
         *  Show pagination for slider
         *  Option available only for `layoutMode: 'slider'`
         *  Values: true or false
         */
        showPagination: true,

        /**
         *  Enable slide to first item (last item)
         *  Option available only for `layoutMode: 'slider'`
         *  Values: true or false
         */
        rewindNav: true,

        /**
         *  Scroll by page and not by item. This option affect next/prev buttons and drag support
         *  Option available only for `layoutMode: 'slider'`
         *  Values: true or false
         */
        scrollByPage: false,

        /**
         *  Default filter for plugin
         *  Option available only for `layoutMode: 'grid'`
         *  Values: strings that represent the filter name(ex: *, .logo, .web-design, .design)
         */
        defaultFilter: '*',

        /**
         *  Enable / disable the deeplinking feature when you click on filters
         *  Option available only for `layoutMode: 'grid'`
         *  Values: true or false
         */
        filterDeeplinking: false,

        /**
         *  Defines which animation to use for items that will be shown or hidden after a filter has been activated.
         *  Option available only for `layoutMode: 'grid'`
         *  The plugin use the best browser features available (css3 transitions and transform, GPU acceleration).
         *  Values: - fadeOut
         *          - quicksand
         *          - bounceLeft
         *          - bounceTop
         *          - bounceBottom
         *          - moveLeft
         *          - slideLeft
         *          - fadeOutTop
         *          - sequentially
         *          - skew
         *          - slideDelay
         *          - rotateSides
         *          - flipOutDelay
         *          - flipOut
         *          - unfold
         *          - foldLeft
         *          - scaleDown
         *          - scaleSides
         *          - frontRow
         *          - flipBottom
         *          - rotateRoom
         */
        animationType: 'fadeOut',

        /**
         *  Adjust the layout grid
         *  Values: - default (no adjustment applied)
         *          - alignCenter (align the grid on center of the page)
         *          - responsive (use a fluid grid to resize the grid)
         */
        gridAdjustment: 'responsive',

        /**
         * Define `media queries` for columns layout.
         * Format: [{width: a, cols: d}, {width: b, cols: e}, {width: c, cols: f}],
         * where a, b, c are the grid width and d, e, f are the columns displayed.
         * e.g. [{width: 1100, cols: 4}, {width: 800, cols: 3}, {width: 480, cols: 2}] means
         * if (gridWidth >= 1100) => show 4 columns,
         * if (gridWidth >= 800 && gridWidth < 1100) => show 3 columns,
         * if (gridWidth >= 480 && gridWidth < 800) => show 2 columns,
         * if (gridWidth < 480) => show 2 columns
         * Keep in mind that a > b > c
         * This option is available only when `gridAdjustment: 'responsive'`
         * Values:  - array of objects of format: [{width: a, cols: d}, {width: b, cols: e}]
         *          - you can define as many objects as you want
         *          - if this option is `false` Cube Portfolio will adjust the items
         *            width automatically (default option for backward compatibility)
         */
        mediaQueries: false,

        /**
         *  Horizontal gap between items
         *  Values: only integers (ex: 1, 5, 10)
         */
        gapHorizontal: 10,

        /**
         *  Vertical gap between items
         *  Values: only integers (ex: 1, 5, 10)
         */
        gapVertical: 10,

        /**
         *  Caption - the overlay that is shown when you put the mouse over an item
         *  NOTE: If you don't want to have captions set this option to an empty string ( caption: '')
         *  Values: - pushTop
         *          - pushDown
         *          - revealBottom
         *          - revealTop
         *          - moveRight
         *          - moveLeft
         *          - overlayBottomPush
         *          - overlayBottom
         *          - overlayBottomReveal
         *          - overlayBottomAlong
         *          - overlayRightAlong
         *          - minimal
         *          - fadeIn
         *          - zoom
         *          - opacity
         */
        caption: 'pushTop',

        /**
         *  The plugin will display his content based on the following values.
         *  Values: - default (the content will be displayed as soon as possible)
         *          - lazyLoading (the plugin will fully preload the images before displaying the items with a fadeIn effect)
         *          - fadeInToTop (the plugin will fully preload the images before displaying the items with a fadeIn effect from bottom to top)
         *          - sequentially (the plugin will fully preload the images before displaying the items with a sequentially effect)
         *          - bottomToTop (the plugin will fully preload the images before displaying the items with an animation from bottom to top)
         */
        displayType: 'lazyLoading',

        /**
         *  Defines the speed of displaying the items (when `displayType == default` this option will have no effect)
         *  Values: only integers, values in ms (ex: 200, 300, 500)
         */
        displayTypeSpeed: 400,

        /**
         *  This is used to define any clickable elements you wish to use to trigger lightbox popup on click.
         *  Values: strings that represent the elements in the document (DOM selector)
         */
        lightboxDelegate: '.cbp-lightbox',

        /**
         *  Enable / disable gallery mode
         *  Values: true or false
         */
        lightboxGallery: true,

        /**
         *  Attribute of the delegate item that contains caption for lightbox
         *  Values: html atributte
         */
        lightboxTitleSrc: 'data-title',

        /**
         *  Markup of the lightbox counter
         *  Values: html markup
         */
        lightboxCounter: '<div class="cbp-popup-lightbox-counter">{{current}} of {{total}}</div>',

        /**
         *  This is used to define any clickable elements you wish to use to trigger singlePage popup on click.
         *  Values: strings that represent the elements in the document (DOM selector)
         */
        singlePageDelegate: '.cbp-singlePage',

        /**
         *  Enable / disable the deeplinking feature for singlePage popup
         *  Values: true or false
         */
        singlePageDeeplinking: true,

        /**
         *  Enable / disable the sticky navigation for singlePage popup
         *  Values: true or false
         */
        singlePageStickyNavigation: true,

        /**
         *  Markup of the singlePage counter
         *  Values: html markup
         */
        singlePageCounter: '<div class="cbp-popup-singlePage-counter">{{current}} of {{total}}</div>',

        /**
         *  Defines which animation to use when singlePage appear
         *  Values: - left
         *          - fade
         *          - right
         */
        singlePageAnimation: 'left',

        /**
         *  Use this callback to update singlePage content.
         *  The callback will trigger after the singlePage popup will open.
         *  @param url = the href attribute of the item clicked
         *  @param element = the item clicked
         *  Values: function
         */
        singlePageCallback: function(url, element) {
            // to update singlePage content use the following method: this.updateSinglePage(yourContent)
        },

        /**
         *  This is used to define any clickable elements you wish to use to trigger singlePage Inline on click.
         *  Values: strings that represent the elements in the document (DOM selector)
         */
        singlePageInlineDelegate: '.cbp-singlePageInline',

        /**
         *  This is used to define the position of singlePage Inline block
         *  Values: - above ( above current element )
         *          - below ( below current elemnet)
         *          - top ( positon top )
         *          - bottom ( positon bottom )
         */
        singlePageInlinePosition: 'top',

        /**
         *  Push the open panel in focus and at close go back to the former stage
         *  Values: true or false
         */
        singlePageInlineInFocus: true,

        /**
         *  Use this callback to update singlePage Inline content.
         *  The callback will trigger after the singlePage Inline will open.
         *  @param url = the href attribute of the item clicked
         *  @param element = the item clicked
         *  Values: function
         */
        singlePageInlineCallback: function(url, element) {
            // to update singlePage Inline content use the following method: this.updateSinglePageInline(yourContent)
        }

    };

    CubePortfolio.Plugins = {};
    $.fn.cubeportfolio.Constructor = CubePortfolio;

})(jQuery, window, document);

(function($, window, document, undefined) {

    'use strict';

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    var popup = {

        /**
         * init function for popup
         * @param cubeportfolio = cubeportfolio instance
         * @param type =  'lightbox' or 'singlePage'
         */
        init: function(cubeportfolio, type) {
            var t = this,
                currentBlock;

            // remember cubeportfolio instance
            t.cubeportfolio = cubeportfolio;

            // remember if this instance is for lightbox or for singlePage
            t.type = type;

            // remember if the popup is open or not
            t.isOpen = false;

            t.options = t.cubeportfolio.options;

            if (type === 'lightbox') {
                t.cubeportfolio._registerEvent('resizeWindow', function() {
                    t.resizeImage();
                });
            }

            if (type === 'singlePageInline') {

                t.startInline = -1;

                t.height = 0;

                // create markup, css and add events for SinglePageInline
                t._createMarkupSinglePageInline();

                t.cubeportfolio._registerEvent('resizeGrid', function() {
                    if (t.isOpen) {
                        // @todo must add support for this features in the future
                        t.close(); // workaround
                    }
                });

                return;
            }

            // create markup, css and add events for lightbox and singlePage
            t._createMarkup();

            if (type === 'singlePage') {

                t.cubeportfolio._registerEvent('resizeWindow', function() {
                    if (t.options.singlePageStickyNavigation) {

                        var width = t.wrap[0].clientWidth;

                        if (width > 0) {
                            t.navigationWrap.width(width);

                            // set navigation width='window width' to center the divs
                            t.navigation.width(width);
                        }

                    }
                });

                if (t.options.singlePageDeeplinking) {
                    t.url = location.href;

                    if (t.url.slice(-1) === '#') {
                        t.url = t.url.slice(0, -1);
                    }

                    var links = t.url.split('#cbp=');
                    var url = links.shift(); // remove first item

                    $.each(links, function(index, link) {

                        $.each(t.cubeportfolio.blocksOn, function(index1, block) {
                            var singlePage = block.elFront.find(t.options.singlePageDelegate + '[href="' + link + '"]');

                            if (singlePage.length) {
                                currentBlock = singlePage;
                                return false;
                            }

                        });

                        if (currentBlock) {
                            return false;
                        }

                    });

                    if (currentBlock) {

                        t.url = url;

                        var self = currentBlock,
                            gallery = self.attr('data-cbp-singlePage'),
                            blocks = [];

                        if (gallery) {
                            blocks = self.closest($('.cbp-item')).find('[data-cbp-singlePage="' + gallery + '"]');
                        } else {
                            $.each(t.cubeportfolio.blocksOn, function(index, item) {
                                if (item.elFront.not('.cbp-item-off')) {
                                    item.elFront.find(t.options.singlePageDelegate).each(function(index2, el2) {
                                        if (!$(el2).attr('data-cbp-singlePage')) {
                                            blocks.push(el2);
                                        }
                                    });
                                }
                            });
                        }

                        t.openSinglePage(blocks, currentBlock[0]);

                    }

                }
            }

        },

        /**
         * Create markup, css and add events
         */
        _createMarkup: function() {
            var t = this,
                animationCls = '';

            if (t.type === 'singlePage') {
                if (t.options.singlePageAnimation !== 'left') {
                    animationCls = ' cbp-popup-singlePage-' + t.options.singlePageAnimation;
                }
            }

            // wrap element
            t.wrap = $('<div/>', {
                'class': 'cbp-popup-wrap cbp-popup-' + t.type + animationCls,
                'data-action': (t.type === 'lightbox') ? 'close' : ''
            }).on('click.cbp', function(e) {
                if (t.stopEvents) {
                    return;
                }

                var action = $(e.target).attr('data-action');

                if (t[action]) {
                    t[action]();
                    e.preventDefault();
                }
            });

            // content element
            t.content = $('<div/>', {
                'class': 'cbp-popup-content'
            }).appendTo(t.wrap);

            // append loading div
            $('<div/>', {
                'class': 'cbp-popup-loadingBox'
            }).appendTo(t.wrap);

            // add background only for ie8
            if (CubePortfolio.Private.browser === 'ie8') {
                t.bg = $('<div/>', {
                    'class': 'cbp-popup-ie8bg',
                    'data-action': (t.type === 'lightbox') ? 'close' : ''
                }).appendTo(t.wrap);
            }

            // create navigation wrap
            t.navigationWrap = $('<div/>', {
                'class': 'cbp-popup-navigation-wrap'
            }).appendTo(t.wrap);

            // create navigation block
            t.navigation = $('<div/>', {
                'class': 'cbp-popup-navigation'
            }).appendTo(t.navigationWrap);

            // close
            t.closeButton = $('<div/>', {
                'class': 'cbp-popup-close',
                'title': 'Close (Esc arrow key)',
                'data-action': 'close'
            }).appendTo(t.navigation);

            // next
            t.nextButton = $('<div/>', {
                'class': 'cbp-popup-next',
                'title': 'Next (Right arrow key)',
                'data-action': 'next'
            }).appendTo(t.navigation);


            // prev
            t.prevButton = $('<div/>', {
                'class': 'cbp-popup-prev',
                'title': 'Previous (Left arrow key)',
                'data-action': 'prev'
            }).appendTo(t.navigation);


            if (t.type === 'singlePage') {

                if (t.options.singlePageCounter) {
                    // counter for singlePage
                    t.counter = $(t.options.singlePageCounter).appendTo(t.navigation);
                    t.counter.text('');
                }

                t.content.on('click.cbp', t.options.singlePageDelegate, function(e) {
                    e.preventDefault();
                    var i,
                        len = t.dataArray.length,
                        href = this.getAttribute('href');

                    for (i = 0; i < len; i++) {

                        if (t.dataArray[i].url === href) {
                            break;
                        }
                    }

                    t.singlePageJumpTo(i - t.current);

                });

                // if there are some events than overrides the default scroll behaviour don't go to them
                t.wrap.on('mousewheel.cbp' + ' DOMMouseScroll.cbp', function(e) {
                    e.stopImmediatePropagation();
                });

            }

            $(document).on('keydown.cbp', function(e) {

                // if is not open => return
                if (!t.isOpen) {
                    return;
                }

                // if all events are stopped => return
                if (t.stopEvents) {
                    return;
                }

                if (e.keyCode === 37) { // prev key
                    t.prev();
                } else if (e.keyCode === 39) { // next key
                    t.next();
                } else if (e.keyCode === 27) { //esc key
                    t.close();
                }
            });

        },

        _createMarkupSinglePageInline: function() {
            var t = this;

            // wrap element
            t.wrap = $('<div/>', {
                'class': 'cbp-popup-singlePageInline'
            }).on('click.cbp', function(e) {
                if (t.stopEvents) {
                    return;
                }

                var action = $(e.target).attr('data-action');

                if (action && t[action]) {
                    t[action]();
                    e.preventDefault();
                }
            });

            // content element
            t.content = $('<div/>', {
                'class': 'cbp-popup-content'
            }).appendTo(t.wrap);

            // append loading div
            // $('<div/>', {
            //     'class': 'cbp-popup-loadingBox'
            // }).appendTo(t.wrap);

            // create navigation block
            t.navigation = $('<div/>', {
                'class': 'cbp-popup-navigation'
            }).appendTo(t.wrap);

            // close
            t.closeButton = $('<div/>', {
                'class': 'cbp-popup-close',
                'title': 'Close (Esc arrow key)',
                'data-action': 'close'
            }).appendTo(t.navigation);

        },

        destroy: function() {
            var t = this,
                body = $('body');

            // remove off key down
            $(document).off('keydown.cbp');

            // external lightbox and singlePageInline
            body.off('click.cbp', t.options.lightboxDelegate);
            body.off('click.cbp', t.options.singlePageDelegate);

            t.content.off('click.cbp', t.options.singlePageDelegate);

            t.cubeportfolio.$obj.off('click.cbp', t.options.singlePageInlineDelegate);
            t.cubeportfolio.$obj.off('click.cbp', t.options.lightboxDelegate);
            t.cubeportfolio.$obj.off('click.cbp', t.options.singlePageDelegate);

            t.cubeportfolio.$obj.removeClass('cbp-popup-isOpening');

            t.cubeportfolio.$obj.find('.cbp-item').removeClass('cbp-singlePageInline-active');

            t.wrap.remove();
        },

        openLightbox: function(blocks, currentBlock) {
            var t = this,
                i = 0,
                currentBlockHref, tempHref = [],
                element;

            if (t.isOpen) {
                return;
            }

            // remember that the lightbox is open now
            t.isOpen = true;

            // remember to stop all events after the lightbox has been shown
            t.stopEvents = false;

            // array with elements
            t.dataArray = [];

            // reset current
            t.current = null;

            currentBlockHref = currentBlock.getAttribute('href');
            if (currentBlockHref === null) {
                throw new Error('HEI! Your clicked element doesn\'t have a href attribute.');
            }

            $.each(blocks, function(index, item) {
                var href = item.getAttribute('href'),
                    src = href, // default if element is image
                    type = 'isImage', // default if element is image
                    videoLink;

                if ($.inArray(href, tempHref) === -1) {

                    if (currentBlockHref === href) {
                        t.current = i;
                    } else if (!t.options.lightboxGallery) {
                        return;
                    }

                    if (/youtube/i.test(href)) {

                        videoLink = href.substring(href.lastIndexOf('v=') + 2);

                        if (!(/autoplay=/i.test(videoLink))) {
                            videoLink += '&autoplay=1';
                        }

                        videoLink = videoLink.replace(/\?|&/, '?');

                        // create new href
                        src = '//www.youtube.com/embed/' + videoLink;

                        type = 'isYoutube';

                    } else if (/vimeo/i.test(href)) {

                        videoLink = href.substring(href.lastIndexOf('/') + 1);

                        if (!(/autoplay=/i.test(videoLink))) {
                            videoLink += '&autoplay=1';
                        }

                        videoLink = videoLink.replace(/\?|&/, '?');

                        // create new href
                        src = '//player.vimeo.com/video/' + videoLink;

                        type = 'isVimeo';

                    } else if (/ted\.com/i.test(href)) {

                        // create new href
                        src = 'http://embed.ted.com/talks/' + href.substring(href.lastIndexOf('/') + 1) + '.html';

                        type = 'isTed';

                    } else if (/(\.mp4)|(\.ogg)|(\.ogv)|(\.webm)/i.test(href)) {

                        if (href.indexOf('|') !== -1) {
                            // create new href
                            src = href.split('|');
                        } else {
                            // create new href
                            src = href.split('%7C');
                        }

                        type = 'isSelfHosted';

                    }

                    t.dataArray.push({
                        src: src,
                        title: item.getAttribute(t.options.lightboxTitleSrc),
                        type: type
                    });

                    i++;
                }

                tempHref.push(href);
            });


            // total numbers of elements
            t.counterTotal = t.dataArray.length;

            if (t.counterTotal === 1) {
                t.nextButton.hide();
                t.prevButton.hide();
                t.dataActionImg = '';
            } else {
                t.nextButton.show();
                t.prevButton.show();
                t.dataActionImg = 'data-action="next"';
            }

            // append to body
            t.wrap.appendTo(document.body);

            t.scrollTop = $(window).scrollTop();

            t.originalStyle = $('html').attr('style');

            $('html').css({
                overflow: 'hidden',
                paddingRight: window.innerWidth - $(document).width()
            });

            // show the wrapper (lightbox box)
            t.wrap.show();

            // get the current element
            element = t.dataArray[t.current];

            // call function if current element is image or video (iframe)
            t[element.type](element);

        },

        openSinglePage: function(blocks, currentBlock) {
            var t = this,
                i = 0,
                currentBlockHref, tempHref = [];

            if (t.isOpen) {
                return;
            }

            // check singlePageInline and close it
            if (t.cubeportfolio.singlePageInline && t.cubeportfolio.singlePageInline.isOpen) {
                t.cubeportfolio.singlePageInline.close();
            }

            // remember that the lightbox is open now
            t.isOpen = true;

            // remember to stop all events after the popup has been showing
            t.stopEvents = false;

            // array with elements
            t.dataArray = [];

            // reset current
            t.current = null;

            currentBlockHref = currentBlock.getAttribute('href');
            if (currentBlockHref === null) {
                throw new Error('HEI! Your clicked element doesn\'t have a href attribute.');
            }


            $.each(blocks, function(index, item) {
                var href = item.getAttribute('href');

                if ($.inArray(href, tempHref) === -1) {

                    if (currentBlockHref === href) {
                        t.current = i;
                    }

                    t.dataArray.push({
                        url: href,
                        element: item
                    });

                    i++;
                }

                tempHref.push(href);
            });

            // total numbers of elements
            t.counterTotal = t.dataArray.length;

            if (t.counterTotal === 1) {
                t.nextButton.hide();
                t.prevButton.hide();
            } else {
                t.nextButton.show();
                t.prevButton.show();
            }

            // append to body
            t.wrap.appendTo(document.body);

            t.scrollTop = $(window).scrollTop();

            $('html').css({
                overflow: 'hidden',
                paddingRight: window.innerWidth - $(document).width()
            });

            // go to top of the page (reset scroll)
            t.wrap.scrollTop(0);

            // show the wrapper
            t.wrap.show();

            // finish the open animation
            t.finishOpen = 2;

            // if transitionend is not fulfilled
            t.navigationMobile = $();
            t.wrap.one(CubePortfolio.Private.transitionend, function() {
                var width;

                // make the navigation sticky
                if (t.options.singlePageStickyNavigation) {

                    t.wrap.addClass('cbp-popup-singlePage-sticky');

                    width = t.wrap[0].clientWidth;
                    t.navigationWrap.width(width);

                    if (CubePortfolio.Private.browser === 'android' || CubePortfolio.Private.browser === 'ios') {
                        // wrap element
                        t.navigationMobile = $('<div/>', {
                            'class': 'cbp-popup-singlePage cbp-popup-singlePage-sticky',
                            'id': t.wrap.attr('id')
                        }).on('click.cbp', function(e) {
                            if (t.stopEvents) {
                                return;
                            }

                            var action = $(e.target).attr('data-action');

                            if (t[action]) {
                                t[action]();
                                e.preventDefault();
                            }
                        });

                        t.navigationMobile.appendTo(document.body).append(t.navigationWrap);
                    }

                }

                t.finishOpen--;
                if (t.finishOpen <= 0) {
                    t.updateSinglePageIsOpen.call(t);
                }

            });

            if (CubePortfolio.Private.browser === 'ie8' || CubePortfolio.Private.browser === 'ie9') {

                // make the navigation sticky
                if (t.options.singlePageStickyNavigation) {
                    var width = t.wrap[0].clientWidth;

                    t.navigationWrap.width(width);

                    setTimeout(function() {
                        t.wrap.addClass('cbp-popup-singlePage-sticky');
                    }, 1000);

                }

                t.finishOpen--;
            }

            t.wrap.addClass('cbp-popup-loading');

            // force reflow and then add class
            t.wrap.offset();
            t.wrap.addClass('cbp-popup-singlePage-open');

            // change link
            if (t.options.singlePageDeeplinking) {
                // ignore old #cbp from href
                t.url = t.url.split('#cbp=')[0];
                location.href = t.url + '#cbp=' + t.dataArray[t.current].url;
            }

            // run callback function
            if ($.isFunction(t.options.singlePageCallback)) {
                t.options.singlePageCallback.call(t, t.dataArray[t.current].url, t.dataArray[t.current].element);
            }

        },


        openSinglePageInline: function(blocks, currentBlock, fromOpen) {
            var t = this,
                start = 0,
                currentBlockHref,
                tempCurrent,
                cbpitem,
                parentElement;

            fromOpen = fromOpen || false;

            t.fromOpen = fromOpen;

            t.storeBlocks = blocks;
            t.storeCurrentBlock = currentBlock;

            // check singlePageInline and close it
            if (t.isOpen) {

                tempCurrent = $(currentBlock).closest('.cbp-item').index();

                if ((t.dataArray[t.current].url !== currentBlock.getAttribute('href')) || (t.current !== tempCurrent)) {
                    t.cubeportfolio.singlePageInline.close('open', {
                        blocks: blocks,
                        currentBlock: currentBlock,
                        fromOpen: true
                    });

                } else {
                    t.close();
                }

                return;
            }

            // remember that the lightbox is open now
            t.isOpen = true;

            // remember to stop all events after the popup has been showing
            t.stopEvents = false;

            // array with elements
            t.dataArray = [];

            // reset current
            t.current = null;

            currentBlockHref = currentBlock.getAttribute('href');
            if (currentBlockHref === null) {
                throw new Error('HEI! Your clicked element doesn\'t have a href attribute.');
            }

            cbpitem = $(currentBlock).closest('.cbp-item')[0];

            $.each(blocks, function(index, item) {
                if (cbpitem === item.elFront[0]) {
                    t.current = index;
                }
            });

            t.dataArray[t.current] = {
                url: currentBlockHref,
                element: currentBlock
            };

            parentElement = $(t.dataArray[t.current].element).parents('.cbp-item').addClass('cbp-singlePageInline-active');

            // total numbers of elements
            t.counterTotal = blocks.length;

            t.wrap.insertBefore(t.cubeportfolio.wrapper);

            if (t.options.singlePageInlinePosition === 'top') {
                t.startInline = 0;
                t.top = 0;

                t.firstRow = true;
                t.lastRow = false;
            } else if (t.options.singlePageInlinePosition === 'bottom') {
                t.startInline = t.counterTotal;
                t.top = t.cubeportfolio.height;

                t.firstRow = false;
                t.lastRow = true;
            } else if (t.options.singlePageInlinePosition === 'above') {
                t.startInline = t.cubeportfolio.cols * Math.floor(t.current / t.cubeportfolio.cols);
                t.top = blocks[t.current].top;

                if (t.startInline === 0) {
                    t.firstRow = true;
                } else {
                    t.top -= t.options.gapHorizontal;
                    t.firstRow = false;
                }

                t.lastRow = false;
            } else { // below
                t.top = blocks[t.current].top + blocks[t.current].height;
                t.startInline = Math.min(t.cubeportfolio.cols *
                    (Math.floor(t.current / t.cubeportfolio.cols) + 1),
                    t.counterTotal);

                t.firstRow = false;
                t.lastRow = (t.startInline === t.counterTotal) ? true : false;
            }

            t.wrap[0].style.height = t.wrap.outerHeight(true) + 'px';

            // debouncer for inline content
            t.deferredInline = $.Deferred();

            if (t.options.singlePageInlineInFocus) {

                t.scrollTop = $(window).scrollTop();

                var goToScroll = t.cubeportfolio.$obj.offset().top + t.top - 100;

                if (t.scrollTop !== goToScroll) {
                    $('html,body').animate({
                            scrollTop: goToScroll
                        }, 350)
                        .promise()
                        .then(function() {
                            t._resizeSinglePageInline();
                            t.deferredInline.resolve();
                        });
                } else {
                    t._resizeSinglePageInline();
                    t.deferredInline.resolve();
                }
            } else {
                t._resizeSinglePageInline();
                t.deferredInline.resolve();
            }

            t.cubeportfolio.$obj.addClass('cbp-popup-singlePageInline-open');

            t.wrap.css({
                top: t.top
            });

            // register callback function
            if ($.isFunction(t.options.singlePageInlineCallback)) {
                t.options.singlePageInlineCallback.call(t, t.dataArray[t.current].url, t.dataArray[t.current].element);
            }
        },

        _resizeSinglePageInline: function() {
            var t = this,
                i, len, item;

            t.height = (t.firstRow || t.lastRow) ? t.wrap.outerHeight(true) : t.wrap.outerHeight(true) - t.options.gapHorizontal;

            for (i = 0, len = t.storeBlocks.length; i < len; i++) {
                item = t.storeBlocks[i];

                if (i < t.startInline) {
                    if (CubePortfolio.Private.modernBrowser) {
                        item.el[0].style[CubePortfolio.Private.transform] = '';
                        if (item.elClone) {
                            item.elClone[0].style[CubePortfolio.Private.transform] = '';
                        }
                    } else {
                        item.el[0].style.marginTop = '';
                    }
                } else {
                    if (CubePortfolio.Private.modernBrowser) {
                        item.el[0].style[CubePortfolio.Private.transform] = 'translate3d(0px, ' + t.height + 'px, 0)';
                        if (item.elClone) {
                            item.elClone[0].style[CubePortfolio.Private.transform] = 'translate3d(0px, ' + t.height + 'px, 0)';
                        }
                    } else {
                        item.el[0].style.marginTop = t.height + 'px';
                    }
                }

            }

            t.cubeportfolio.obj.style.height = t.cubeportfolio.height + t.height + 'px';

        },

        _revertResizeSinglePageInline: function() {
            var t = this,
                i, len, item;

            // reset deferred object
            t.deferredInline = $.Deferred();

            for (i = 0, len = t.storeBlocks.length; i < len; i++) {
                item = t.storeBlocks[i];

                if (CubePortfolio.Private.modernBrowser) {
                    item.el[0].style[CubePortfolio.Private.transform] = '';
                    if (item.elClone) {
                        item.elClone[0].style[CubePortfolio.Private.transform] = '';
                    }
                } else {
                    item.el[0].style.marginTop = '';
                }

            }

            t.cubeportfolio.obj.style.height = t.cubeportfolio.height + 'px';
        },

        appendScriptsToWrap: function(scripts) {
            var t = this,
                index = 0,
                loadScripts = function(item) {
                    var script = document.createElement('script'),
                        src = item.src;

                    script.type = 'text/javascript';

                    if (script.readyState) { // ie
                        script.onreadystatechange = function() {
                            if (script.readyState == 'loaded' || script.readyState == 'complete') {
                                script.onreadystatechange = null;
                                index++;
                                if (scripts[index]) {
                                    loadScripts(scripts[index]);
                                }
                            }
                        };
                    } else {
                        script.onload = function() {
                            index++;
                            if (scripts[index]) {
                                loadScripts(scripts[index]);
                            }
                        };
                    }

                    if (src) {
                        script.src = src;
                    } else {
                        script.text = item.text;
                    }

                    t.content[0].appendChild(script);

                };

            loadScripts(scripts[0]);
        },

        updateSinglePage: function(html, scripts, isWrap) {
            var t = this,
                counterMarkup,
                animationFinish;

            t.content.addClass('cbp-popup-content').removeClass('cbp-popup-content-basic');

            if (isWrap === false) {
                t.content.removeClass('cbp-popup-content').addClass('cbp-popup-content-basic');
            }

            // update counter navigation
            if (t.counter) {
                counterMarkup = $(t._getCounterMarkup(t.options.singlePageCounter, t.current + 1, t.counterTotal));
                t.counter.text(counterMarkup.text());
            }

            t.content.html(html);

            if (scripts) {
                t.appendScriptsToWrap(scripts);
            }

            t.finishOpen--;

            if (t.finishOpen <= 0) {
                t.updateSinglePageIsOpen.call(t);
            }
        },

        updateSinglePageIsOpen: function() {
            var t = this,
                selectorSlider;

            t.wrap.addClass('cbp-popup-ready');
            t.wrap.removeClass('cbp-popup-loading');

            // instantiate slider if exists
            selectorSlider = t.content.find('.cbp-slider');
            if (selectorSlider) {
                selectorSlider.find('.cbp-slider-item').addClass('cbp-item');
                t.slider = selectorSlider.cubeportfolio({
                    layoutMode: 'slider',
                    mediaQueries: [{
                        width: 1,
                        cols: 1
                    }],
                    gapHorizontal: 0,
                    gapVertical: 0,
                    caption: '',
                    ratioAuto: true, // wp version only
                });
            } else {
                t.slider = null;
            }

            // scroll bug on android and ios
            if (CubePortfolio.Private.browser === 'android' || CubePortfolio.Private.browser === 'ios') {
                $('html').css({
                    position: 'fixed'
                });
            }

            // trigger public event
            t.cubeportfolio.$obj.trigger('updateSinglePageComplete.cbp');

        },


        updateSinglePageInline: function(html, scripts) {
            var t = this;

            t.content.html(html);

            if (scripts) {
                t.appendScriptsToWrap(scripts);
            }

            t.singlePageInlineIsOpen.call(t);

        },

        singlePageInlineIsOpen: function() {
            var t = this;

            function finishLoading() {
                t.wrap.addClass('cbp-popup-singlePageInline-ready');
                t.wrap[0].style.height = '';

                t._resizeSinglePageInline();

                // trigger public event
                t.cubeportfolio.$obj.trigger('updateSinglePageInlineComplete.cbp');
            }

            // wait to load all images
            t.cubeportfolio._load(t.wrap, function() {


                // instantiate slider if exists
                var selectorSlider = t.content.find('.cbp-slider');

                if (selectorSlider.length) {
                    selectorSlider.find('.cbp-slider-item').addClass('cbp-item');

                    selectorSlider.one('initComplete.cbp', function() {
                        t.deferredInline.done(finishLoading);
                    });

                    selectorSlider.on('pluginResize.cbp', function() {
                        t.deferredInline.done(finishLoading);
                    });

                    t.slider = selectorSlider.cubeportfolio({
                        layoutMode: 'slider',
                        displayType: 'default',
                        mediaQueries: [{
                            width: 1,
                            cols: 1
                        }],
                        gapHorizontal: 0,
                        gapVertical: 0,
                        caption: '',
                        ratioAuto: true, // wp version only
                    });
                } else {
                    t.slider = null;
                    t.deferredInline.done(finishLoading);
                }

            });

        },


        isImage: function(el) {
            var t = this,
                img = new Image();

            t.tooggleLoading(true);

            if ($('<img src="' + el.src + '">').is('img:uncached')) {

                $(img).on('load.cbp' + ' error.cbp', function() {

                    t.updateImagesMarkup(el.src, el.title, t._getCounterMarkup(t.options.lightboxCounter, t.current + 1, t.counterTotal));

                    t.tooggleLoading(false);

                });
                img.src = el.src;

            } else {

                t.updateImagesMarkup(el.src, el.title, t._getCounterMarkup(t.options.lightboxCounter, t.current + 1, t.counterTotal));

                t.tooggleLoading(false);
            }
        },

        isVimeo: function(el) {
            var t = this;

            t.updateVideoMarkup(el.src, el.title, t._getCounterMarkup(t.options.lightboxCounter, t.current + 1, t.counterTotal));
        },

        isYoutube: function(el) {
            var t = this;
            t.updateVideoMarkup(el.src, el.title, t._getCounterMarkup(t.options.lightboxCounter, t.current + 1, t.counterTotal));

        },

        isTed: function(el) {
            var t = this;
            t.updateVideoMarkup(el.src, el.title, t._getCounterMarkup(t.options.lightboxCounter, t.current + 1, t.counterTotal));
        },

        isSelfHosted: function(el) {
            var t = this;
            t.updateSelfHostedVideo(el.src, el.title, t._getCounterMarkup(t.options.lightboxCounter, t.current + 1, t.counterTotal));
        },

        _getCounterMarkup: function(markup, current, total) {
            if (!markup.length) {
                return '';
            }

            var mapObj = {
                current: current,
                total: total
            };

            return markup.replace(/\{\{current}}|\{\{total}}/gi, function(matched) {
                return mapObj[matched.slice(2, -2)];
            });
        },

        updateSelfHostedVideo: function(src, title, counter) {
            var t = this,
                i;

            t.wrap.addClass('cbp-popup-lightbox-isIframe');

            var markup = '<div class="cbp-popup-lightbox-iframe">' +
                '<video controls="controls" height="auto" style="width: 100%">';

            for (i = 0; i < src.length; i++) {
                if (/(\.mp4)/i.test(src[i])) {
                    markup += '<source src="' + src[i] + '" type="video/mp4">';
                } else if (/(\.ogg)|(\.ogv)/i.test(src[i])) {
                    markup += '<source src="' + src[i] + '" type="video/ogg">';
                } else if (/(\.webm)/i.test(src[i])) {
                    markup += '<source src="' + src[i] + '" type="video/webm">';
                }
            }

            markup += 'Your browser does not support the video tag.' +
                '</video>' +
                '<div class="cbp-popup-lightbox-bottom">' +
                ((title) ? '<div class="cbp-popup-lightbox-title">' + title + '</div>' : '') +
                counter +
                '</div>' +
                '</div>';

            t.content.html(markup);

            t.wrap.addClass('cbp-popup-ready');

            t.preloadNearbyImages();
        },

        updateVideoMarkup: function(src, title, counter) {
            var t = this;
            t.wrap.addClass('cbp-popup-lightbox-isIframe');

            var markup = '<div class="cbp-popup-lightbox-iframe">' +
                '<iframe src="' + src + '" frameborder="0" allowfullscreen scrolling="no"></iframe>' +
                '<div class="cbp-popup-lightbox-bottom">' +
                ((title) ? '<div class="cbp-popup-lightbox-title">' + title + '</div>' : '') +
                counter +
                '</div>' +
                '</div>';

            t.content.html(markup);
            t.wrap.addClass('cbp-popup-ready');
            t.preloadNearbyImages();
        },

        updateImagesMarkup: function(src, title, counter) {
            var t = this;

            t.wrap.removeClass('cbp-popup-lightbox-isIframe');

            var markup = '<div class="cbp-popup-lightbox-figure">' +
                '<img src="' + src + '" class="cbp-popup-lightbox-img" ' + t.dataActionImg + ' />' +
                '<div class="cbp-popup-lightbox-bottom">' +
                ((title) ? '<div class="cbp-popup-lightbox-title">' + title + '</div>' : '') +
                counter +
                '</div>' +
                '</div>';

            t.content.html(markup);

            t.wrap.addClass('cbp-popup-ready');

            t.resizeImage();

            t.preloadNearbyImages();
        },

        next: function() {
            var t = this;
            t[t.type + 'JumpTo'](1);
        },

        prev: function() {
            var t = this;
            t[t.type + 'JumpTo'](-1);
        },

        lightboxJumpTo: function(index) {
            var t = this,
                el;

            t.current = t.getIndex(t.current + index);

            // get the current element
            el = t.dataArray[t.current];

            // call function if current element is image or video (iframe)
            t[el.type](el);
        },


        singlePageJumpTo: function(index) {
            var t = this;

            t.current = t.getIndex(t.current + index);

            // register singlePageCallback function
            if ($.isFunction(t.options.singlePageCallback)) {
                t.resetWrap();

                // go to top of the page (reset scroll)
                t.wrap.scrollTop(0);

                t.wrap.addClass('cbp-popup-loading');
                t.options.singlePageCallback.call(t, t.dataArray[t.current].url, t.dataArray[t.current].element);

                if (t.options.singlePageDeeplinking) {
                    location.href = t.url + '#cbp=' + t.dataArray[t.current].url;
                }
            }
        },

        resetWrap: function() {
            var t = this;

            if (t.type === 'singlePage' && t.options.singlePageDeeplinking) {
                location.href = t.url + '#';
            }
        },

        getIndex: function(index) {
            var t = this;

            // go to interval [0, (+ or -)this.counterTotal.length - 1]
            index = index % t.counterTotal;

            // if index is less then 0 then go to interval (0, this.counterTotal - 1]
            if (index < 0) {
                index = t.counterTotal + index;
            }

            return index;
        },

        close: function(method, data) {
            var t = this;

            function finishClose() {
                // reset content
                t.content.html('');

                // hide the wrap
                t.wrap.detach();

                t.cubeportfolio.$obj.removeClass('cbp-popup-singlePageInline-open cbp-popup-singlePageInline-close');

                if (method === 'promise') {
                    if ($.isFunction(data.callback)) {
                        data.callback.call(t.cubeportfolio);
                    }
                }
            }

            function checkFocusInline() {
                if (t.options.singlePageInlineInFocus && method !== 'promise') {
                    $('html,body').animate({
                            scrollTop: t.scrollTop
                        }, 350)
                        .promise()
                        .then(function() {
                            finishClose();
                        });
                } else {
                    finishClose();
                }
            }

            // now the popup is closed
            t.isOpen = false;

            if (t.type === 'singlePageInline') {

                if (method === 'open') {

                    t.wrap.removeClass('cbp-popup-singlePageInline-ready');

                    $(t.dataArray[t.current].element).closest('.cbp-item').removeClass('cbp-singlePageInline-active');

                    t.openSinglePageInline(data.blocks, data.currentBlock, data.fromOpen);

                } else {

                    t.height = 0;

                    t._revertResizeSinglePageInline();

                    t.wrap.removeClass('cbp-popup-singlePageInline-ready');

                    t.cubeportfolio.$obj.addClass('cbp-popup-singlePageInline-close');

                    t.startInline = -1;

                    t.cubeportfolio.$obj.find('.cbp-item').removeClass('cbp-singlePageInline-active');

                    if (CubePortfolio.Private.modernBrowser) {
                        t.wrap.one(CubePortfolio.Private.transitionend, function() {
                            checkFocusInline();
                        });
                    } else {
                        checkFocusInline();
                    }
                }

            } else if (t.type === 'singlePage') {

                t.resetWrap();

                t.wrap.removeClass('cbp-popup-ready');

                // scroll bug on android and ios
                if (CubePortfolio.Private.browser === 'android' || CubePortfolio.Private.browser === 'ios') {
                    $('html').css({
                        position: ''
                    });

                    t.navigationWrap.appendTo(t.wrap);
                    t.navigationMobile.remove();
                }

                $(window).scrollTop(t.scrollTop);

                // weird bug on mozilla. fixed with setTimeout
                setTimeout(function() {
                    t.stopScroll = true;

                    t.navigationWrap.css({
                        top: t.wrap.scrollTop()
                    });

                    t.wrap.removeClass('cbp-popup-singlePage-open cbp-popup-singlePage-sticky');

                    if (CubePortfolio.Private.browser === 'ie8' || CubePortfolio.Private.browser === 'ie9') {
                        // reset content
                        t.content.html('');

                        // hide the wrap
                        t.wrap.detach();

                        $('html').css({
                            overflow: '',
                            paddingRight: '',
                            position: ''
                        });

                        t.navigationWrap.removeAttr('style');
                    }

                }, 0);

                t.wrap.one(CubePortfolio.Private.transitionend, function() {

                    // reset content
                    t.content.html('');

                    // hide the wrap
                    t.wrap.detach();

                    $('html').css({
                        overflow: '',
                        paddingRight: '',
                        position: ''
                    });

                    t.navigationWrap.removeAttr('style');

                });

            } else {

                if (t.originalStyle) {
                    $('html').attr('style', t.originalStyle);
                } else {
                    $('html').css({
                        overflow: '',
                        paddingRight: ''
                    });
                }

                $(window).scrollTop(t.scrollTop);

                // reset content
                t.content.html('');

                // hide the wrap
                t.wrap.detach();

            }
        },

        tooggleLoading: function(state) {
            var t = this;

            t.stopEvents = state;
            t.wrap[(state) ? 'addClass' : 'removeClass']('cbp-popup-loading');
        },

        resizeImage: function() {
            // if lightbox is not open go out
            if (!this.isOpen) {
                return;
            }

            var height = $(window).height(),
                img = this.content.find('img'),
                padding = parseInt(img.css('margin-top'), 10) + parseInt(img.css('margin-bottom'), 10);

            img.css('max-height', (height - padding) + 'px');
        },

        preloadNearbyImages: function() {
            var arr = [],
                img, t = this,
                src;

            arr.push(t.getIndex(t.current + 1));
            arr.push(t.getIndex(t.current + 2));
            arr.push(t.getIndex(t.current + 3));
            arr.push(t.getIndex(t.current - 1));
            arr.push(t.getIndex(t.current - 2));
            arr.push(t.getIndex(t.current - 3));

            for (var i = arr.length - 1; i >= 0; i--) {
                if (t.dataArray[arr[i]].type === 'isImage') {
                    src = t.dataArray[arr[i]].src;
                    img = new Image();

                    if ($('<img src="' + src + '">').is('img:uncached')) {
                        img.src = src;
                    }
                }
            }
        }

    };


    function PopUp(parent) {
        var t = this;

        t.parent = parent;

        // if lightboxShowCounter is false, put lightboxCounter to ''
        if (parent.options.lightboxShowCounter === false) {
            parent.options.lightboxCounter = '';
        }

        // if singlePageShowCounter is false, put singlePageCounter to ''
        if (parent.options.singlePageShowCounter === false) {
            parent.options.singlePageCounter = '';
        }

        // @todo - schedule this in  future
        t.run();

    }

    var lightboxInit = false,
        singlePageInit = false;

    PopUp.prototype.run = function() {
        var t = this,
            p = t.parent,
            body = $(document.body);

        // default value for lightbox
        p.lightbox = null;

        // LIGHTBOX
        if (p.$obj.find(p.options.lightboxDelegate) && !lightboxInit) {

            // init only one time @todo
            lightboxInit = true;

            p.lightbox = Object.create(popup);

            p.lightbox.init(p, 'lightbox');

            body.on('click.cbp', p.options.lightboxDelegate, function(e) {
                e.preventDefault();

                var self = $(this),
                    gallery = self.attr('data-cbp-lightbox'),
                    scope = t.detectScope(self),
                    cbp = scope.data('cubeportfolio'),
                    blocks = [];

                // is inside a cbp
                if (cbp) {

                    $.each(cbp.blocksOn, function(index, item) {
                        if (item.elFront.not('.cbp-item-off')) {
                            item.elFront.find(p.options.lightboxDelegate).each(function(index2, el2) {
                                if (gallery) {
                                    if ($(el2).attr('data-cbp-lightbox') === gallery) {
                                        blocks.push(el2);
                                    }
                                } else {
                                    blocks.push(el2);
                                }
                            });
                        }
                    });

                } else {

                    if (gallery) {
                        blocks = scope.find(p.options.lightboxDelegate + '[data-cbp-lightbox=' + gallery + ']');
                    } else {
                        blocks = scope.find(p.options.lightboxDelegate);
                    }
                }

                p.lightbox.openLightbox(blocks, self[0]);
            });
        }

        // default value for singlePage
        p.singlePage = null;

        // SINGLEPAGE
        if (p.$obj.find(p.options.singlePageDelegate) && !singlePageInit) {

            // init only one time @todo
            singlePageInit = true;

            p.singlePage = Object.create(popup);

            p.singlePage.init(p, 'singlePage');

            body.on('click.cbp', p.options.singlePageDelegate, function(e) {
                e.preventDefault();

                var self = $(this),
                    gallery = self.attr('data-cbp-singlePage'),
                    scope = t.detectScope(self),
                    cbp = scope.data('cubeportfolio'),
                    blocks = [];

                // is inside a cbp
                if (cbp) {
                    $.each(cbp.blocksOn, function(index, item) {
                        if (item.elFront.not('.cbp-item-off')) {
                            item.elFront.find(p.options.singlePageDelegate).each(function(index2, el2) {
                                if (gallery) {
                                    if ($(el2).attr('data-cbp-singlePage') === gallery) {
                                        blocks.push(el2);
                                    }
                                } else {
                                    blocks.push(el2);
                                }
                            });
                        }
                    });

                } else {

                    if (gallery) {
                        blocks = scope.find(p.options.singlePageDelegate + '[data-cbp-singlePage=' + gallery + ']');
                    } else {
                        blocks = scope.find(p.options.singlePageDelegate);
                    }

                }

                p.singlePage.openSinglePage(blocks, self[0]);
            });
        }

        // default value for singlePageInline
        p.singlePageInline = null;

        // SINGLEPAGEINLINE
        if (p.$obj.find(p.options.singlePageInlineDelegate)) {

            p.singlePageInline = Object.create(popup);

            p.singlePageInline.init(p, 'singlePageInline');

            p.$obj.on('click.cbp', p.options.singlePageInlineDelegate, function(e) {
                e.preventDefault();
                p.singlePageInline.openSinglePageInline(p.blocksOn, this);
            });

        }
    };

    PopUp.prototype.detectScope = function(item) {
        var singlePageInline,
            singlePage,
            cbp;

        singlePageInline = item.closest('.cbp-popup-singlePageInline');
        if (singlePageInline.length) {
            cbp = item.closest('.cbp', singlePageInline[0]);
            return (cbp.length) ? cbp : singlePageInline;
        }

        singlePage = item.closest('.cbp-popup-singlePage');
        if (singlePage.length) {
            cbp = item.closest('.cbp', singlePage[0]);
            return (cbp.length) ? cbp : singlePage;
        }

        cbp = item.closest('.cbp');
        return (cbp.length) ? cbp : $(document.body);

    };

    PopUp.prototype.destroy = function() {
        var p = this.parent;

        $(document.body).off('click.cbp');

        // @todo - remove thiese from here
        lightboxInit = false;
        singlePageInit = false;

        // destroy lightbox if enabled
        if (p.lightbox) {
            p.lightbox.destroy();
        }

        // destroy singlePage if enabled
        if (p.singlePage) {
            p.singlePage.destroy();
        }

        // destroy singlePage inline if enabled
        if (p.singlePageInline) {
            p.singlePageInline.destroy();
        }
    };

    CubePortfolio.Plugins.PopUp = function(parent) {
        return new PopUp(parent);
    };

})(jQuery, window, document);

(function($, window, document, undefined) {

    'use strict';

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    CubePortfolio.Private = {
        /**
         * Check if cubeportfolio instance exists on current element
         */
        checkInstance: function(method) {
            var t = $.data(this, 'cubeportfolio');

            if (!t) {
                throw new Error('cubeportfolio is not initialized. Initialize it before calling ' + method + ' method!');
            }

            return t;
        },

        /**
         * Get info about client browser
         */
        browserInfo: function() {
            var t = CubePortfolio.Private,
                appVersion = navigator.appVersion,
                transition, animation, perspective;

            if (appVersion.indexOf('MSIE 8.') !== -1) { // ie8
                t.browser = 'ie8';
            } else if (appVersion.indexOf('MSIE 9.') !== -1) { // ie9
                t.browser = 'ie9';
            } else if (appVersion.indexOf('MSIE 10.') !== -1) { // ie10
                t.browser = 'ie10';
            } else if (window.ActiveXObject || 'ActiveXObject' in window) { // ie11
                t.browser = 'ie11';
            } else if ((/android/gi).test(appVersion)) { // android
                t.browser = 'android';
            } else if ((/iphone|ipad|ipod/gi).test(appVersion)) { // ios
                t.browser = 'ios';
            } else if ((/chrome/gi).test(appVersion)) {
                t.browser = 'chrome';
            } else {
                t.browser = '';
            }

            // check if perspective is available
            perspective = t.styleSupport('perspective');

            // if perspective is not available => no modern browser
            if (typeof perspective === undefined) {
                return;
            }

            transition = t.styleSupport('transition');

            t.transitionend = {
                WebkitTransition: 'webkitTransitionEnd',
                transition: 'transitionend'
            }[transition];

            animation = t.styleSupport('animation');

            t.animationend = {
                WebkitAnimation: 'webkitAnimationEnd',
                animation: 'animationend'
            }[animation];

            t.animationDuration = {
                WebkitAnimation: 'webkitAnimationDuration',
                animation: 'animationDuration'
            }[animation];

            t.animationDelay = {
                WebkitAnimation: 'webkitAnimationDelay',
                animation: 'animationDelay'
            }[animation];

            t.transform = t.styleSupport('transform');

            if (transition && animation && t.transform) {
                t.modernBrowser = true;
            }

        },


        /**
         * Feature testing for css3
         */
        styleSupport: function(prop) {
            var supportedProp,
                // capitalize first character of the prop to test vendor prefix
                webkitProp = 'Webkit' + prop.charAt(0).toUpperCase() + prop.slice(1),
                div = document.createElement('div');

            // browser supports standard CSS property name
            if (prop in div.style) {
                supportedProp = prop;
            } else if (webkitProp in div.style) {
                supportedProp = webkitProp;
            }

            // avoid memory leak in IE
            div = null;

            return supportedProp;
        }

    };

    CubePortfolio.Private.browserInfo();

})(jQuery, window, document);

(function($, window, document, undefined) {

    'use strict';

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    CubePortfolio.Public = {

        /*
         * Init the plugin
         */
        init: function(options, callback) {
            new CubePortfolio(this, options, callback);
        },

        /*
         * Destroy the plugin
         */
        destroy: function(callback) {
            var t = CubePortfolio.Private.checkInstance.call(this, 'destroy');

            // remove data
            $.removeData(this, 'cubeportfolio');

            // remove data from blocks
            $.each(t.blocks, function() {
                $.removeData(this, 'transformFn');
                $.removeData(this, 'cbp-wxh');
            });

            // remove loading class and .cbp on container
            t.$obj.removeClass('cbp cbp-ready ' + 'cbp-cols-' + t.cols).removeAttr('style');

            // remove class from ul
            t.$ul.removeClass('cbp-wrapper');

            // remove off resize event
            $(window).off('resize.cbp');

            t.$obj.off('.cbp');
            $(document).off('.cbp');

            // reset blocks
            t.blocks.removeClass('cbp-item-off').removeAttr('style');

            t.blocks.find('.cbp-item-wrapper').children().unwrap();

            if (t.options.caption) {
                t._captionDestroy();
            }

            t._destroySlider();

            // remove .cbp-wrapper-outer
            t.$ul.unwrap();

            // remove .cbp-wrapper
            if (t.addedWrapp) {
                t.blocks.unwrap();
            }

            $.each(t._plugins, function(i, item) {
                if (typeof item.destroy === 'function') {
                    item.destroy();
                }
            });

            if ($.isFunction(callback)) {
                callback.call(t);
            }
        },

        /*
         * Filter the plugin by filterName
         */
        filter: function(filterName, callback) {
            var t = CubePortfolio.Private.checkInstance.call(this, 'filter'),
                off2onBlocks, on2offBlocks, url;

            // register callback function
            if ($.isFunction(callback)) {
                t._registerEvent('filterFinish', callback, true);
            }

            if (t.isAnimating || t.defaultFilter === filterName) {
                return;
            }

            t.isAnimating = true;
            t.defaultFilter = filterName;

            if (t.singlePageInline && t.singlePageInline.isOpen) {
                t.singlePageInline.close('promise', {
                    callback: function() {
                        t._filter(filterName);
                    }
                });
            } else {
                t._filter(filterName);
            }

            if (t.options.filterDeeplinking) {

                url = location.href.replace(/#cbpf=(.*?)([#|?&]|$)/gi, '');

                location.href = url + '#cbpf=' + filterName;

                if (t.singlePage && t.singlePage.url) {
                    t.singlePage.url = location.href;
                }
            }
        },

        /*
         * Show counter for filters
         */
        showCounter: function(elems, callback) {
            var t = CubePortfolio.Private.checkInstance.call(this, 'showCounter');

            t.elems = elems;

            $.each(elems, function() {
                var el = $(this),
                    filterName = el.data('filter'),
                    count;

                count = t.blocks.filter(filterName).length;
                el.find('.cbp-filter-counter').text(count);
            });

            if ($.isFunction(callback)) {
                callback.call(t);
            }
        },

        /*
         * ApendItems elements
         */
        appendItems: function(items, callback) {
            var t = CubePortfolio.Private.checkInstance.call(this, 'appendItems');

            if (t.singlePageInline && t.singlePageInline.isOpen) {
                t.singlePageInline.close('promise', {
                    callback: function() {
                        t._addItems(items, callback);
                    }
                });
            } else {
                t._addItems(items, callback);
            }
        },

    };

})(jQuery, window, document);

// Utility
if (typeof Object.create !== 'function') {
    Object.create = function(obj) {
        function F() {}
        F.prototype = obj;
        return new F();
    };
}

// jquery new filter for images uncached
jQuery.expr[':'].uncached = function(obj) {
    // Ensure we are dealing with an `img` element with a valid `src` attribute.
    if (!jQuery(obj).is('img[src][src!=""]')) {
        return false;
    }

    // Firefox's `complete` property will always be `true` even if the image has not been downloaded.
    // Doing it this way works in Firefox.
    var img = new Image();
    img.src = obj.src;

    // http://stackoverflow.com/questions/1977871/check-if-an-image-is-loaded-no-errors-in-javascript
    // During the onload event, IE correctly identifies any images that
    // weren�t downloaded as not complete. Others should too. Gecko-based
    // browsers act like NS4 in that they report this incorrectly.
    if (!img.complete) {
        return true;
    }

    // However, they do have two very useful properties: naturalWidth and
    // naturalHeight. These give the true size of the image. If it failed
    // to load, either of these should be zero.
    if (img.naturalWidth !== undefined && img.naturalWidth === 0) {
        return true;
    }

    // No other way of checking: assume it�s ok.
    return false;
};

// http://paulirish.com/2011/requestanimationframe-for-smart-animating/
// http://my.opera.com/emoller/blog/2011/12/20/requestanimationframe-for-smart-er-animating

// requestAnimationFrame polyfill by Erik M�ller. fixes from Paul Irish and Tino Zijdel

// MIT license

(function() {
    var lastTime = 0;
    var vendors = ['moz', 'webkit'];
    for (var x = 0; x < vendors.length && !window.requestAnimationFrame; ++x) {
        window.requestAnimationFrame = window[vendors[x] + 'RequestAnimationFrame'];
        window.cancelAnimationFrame = window[vendors[x] + 'CancelAnimationFrame'] || window[vendors[x] + 'CancelRequestAnimationFrame'];
    }

    if (!window.requestAnimationFrame)
        window.requestAnimationFrame = function(callback, element) {
            var currTime = new Date().getTime();
            var timeToCall = Math.max(0, 16 - (currTime - lastTime));
            var id = window.setTimeout(function() {
                    callback(currTime + timeToCall);
                },
                timeToCall);
            lastTime = currTime + timeToCall;
            return id;
        };

    if (!window.cancelAnimationFrame)
        window.cancelAnimationFrame = function(id) {
            clearTimeout(id);
        };
}());

(function($, window, document, undefined) {

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    function AnimationClassic(parent) {
        var t = this;

        t.parent = parent;

        parent._registerEvent('filterBeforeLayout', function() {
            parent.$obj.addClass('cbp-animation-' + parent.options.animationType);
        }, true);

        parent._registerEvent('filterBeforeLayout', function() {
            parent.$obj.addClass('cbp-transition-active');
        });

        parent.filterLayout = t.filterLayout;

        // add this if defaultFilter is not *
        parent._registerEvent('delayFrame', function() {
            var item, i;

            if (parent.defaultFilter === '*') {
                return;
            }

            for (i = parent.blocksObj.length - 1; i >= 0; i--) {
                item = parent.blocksObj[i];

                if (item.el.hasClass('cbp-item-off')) {
                    item.el[0].style.visibility = 'hidden';
                }
            }
        });
    }

    AnimationClassic.prototype.filterLayout = function(filterName) {
        var t = this,
            item, i, animatedEl;

        for (i = t.blocksObj.length - 1; i >= 0; i--) {
            item = t.blocksObj[i];

            if (item.el.is(filterName)) {

                if (item.el.hasClass('cbp-item-off')) {
                    item.wrapper[0].setAttribute('class', 'cbp-item-wrapper cbp-item-off2on');

                    item.el[0].style.left = item.leftNew + 'px';
                    item.el[0].style.top = item.topNew + 'px';

                    // add this if defaultFilter is not *
                    item.el[0].style.visibility = '';

                    item.el.removeClass('cbp-item-off');
                } else {
                    // move this element
                    item.el[0].style[CubePortfolio.Private.transform] = 'translate3d(' + (item.leftNew - item.left) + 'px, ' + (item.topNew - item.top) + 'px, 0)';
                    animatedEl = item.el;
                }

            } else {

                if (!item.el.hasClass('cbp-item-off')) {
                    item.wrapper[0].setAttribute('class', 'cbp-item-wrapper cbp-item-on2off');
                }

                item.el.addClass('cbp-item-off');
            }
        }


        function transitionend() {
            var i, item;

            t.$obj.removeClass('cbp-transition-active');

            for (i = t.blocksObj.length - 1; i >= 0; i--) {
                item = t.blocksObj[i];

                item.left = item.leftNew;
                item.top = item.topNew;

                item.el[0].style.left = item.left + 'px';
                item.el[0].style.top = item.top + 'px';
                item.el[0].style[CubePortfolio.Private.transform] = '';
            }

            t.filterDeferred.resolve();
        }

        if (!animatedEl) {
            transitionend();
        } else {
            animatedEl.one(CubePortfolio.Private.transitionend, function() {
                transitionend();
            });
        }

    };

    AnimationClassic.prototype.destroy = function() {
        var parent = this.parent;
        parent.$obj.removeClass('cbp-animation-' + parent.options.animationType);
    };

    CubePortfolio.Plugins.AnimationClassic = function (parent) {

        if (!CubePortfolio.Private.modernBrowser || $.inArray(parent.options.animationType, ['quicksand', 'fadeOut', 'flipOut', 'flipBottom', 'scaleSides', 'skew', 'boxShadow']) < 0) {
            return null;
        }

        return new AnimationClassic(parent);
    };

})(jQuery, window, document);

(function($, window, document, undefined) {

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    function AnimationClone(parent) {
        var t = this,
            p;

        t.parent = p = parent;

        parent._registerEvent('filterBeforeLayout', function() {
            parent.$ulClone[0].style.display = '';
            parent.$obj.addClass('cbp-animation-' + parent.options.animationType);
        }, true);

        parent._registerEvent('initFinish', function() {
            parent.$ulClone = parent.$ul.clone();
            parent.$ulClone[0].style.display = 'none';

            parent.$ulClone.children('.cbp-item').each(function(index, el) {
                el = $(el);

                parent.blocksObj[index].elClone = el;
                parent.blocksObj[index].wrapperClone = el.children();
            });

            parent.$ulClone.insertAfter(parent.$ul);

            parent.wrapperFront = true;
        });

        parent._registerEvent('filterBeforeLayout', function() {
            var i, len, item, wrapper;

            parent.$obj.addClass('cbp-transition-active');

            // is $ul here
            if (parent.wrapperFront) {
                parent.$ul.removeClass('cbp-wrapper-front');
                parent.$ulClone.addClass('cbp-wrapper-front');

                parent.wrapperFront = false;

            } else { // is clone
                parent.$ul.addClass('cbp-wrapper-front');
                parent.$ulClone.removeClass('cbp-wrapper-front');

                parent.wrapperFront = true;
            }

        });

        parent._registerEvent('addItemsToDOM', function(items) {
            var newItems = items.clone(),
                lenItems = newItems.length,
                lenObj = parent.blocksObj.length;

            newItems.appendTo(parent.$ulClone);

            newItems.each(function(index, el) {
                el = $(el);
                parent.blocksObj[lenObj + index - lenItems].elClone = el;
                parent.blocksObj[lenObj + index - lenItems].wrapperClone = el.children();

                if (!parent.wrapperFront) {
                    parent.blocksObj[lenObj + index - lenItems].elFront = el;
                }
            });

        });

        parent.filterLayout = t.filterLayout;

    }

    AnimationClone.prototype.filterLayout = function(filterName) {
        var t = this,
            // delayBack = 0,
            item, i, len, elFront, elBack, wrapperFront, wrapperBack, animatedEl;

        for (i = 0, len = t.blocksObj.length; i < len; i++) {
            item = t.blocksObj[i];

            if (t.wrapperFront) {
                elFront = item.elClone;
                elBack = item.el;
                wrapperFront = item.wrapperClone;
                wrapperBack = item.wrapper;

                // keep track what el is in front
                item.elFront = item.el;

            } else {
                elFront = item.el;
                elBack = item.elClone;
                wrapperFront = item.wrapper;
                wrapperBack = item.wrapperClone;

                // keep track what el is in front
                item.elFront = item.elClone;
            }

            if (!elFront.hasClass('cbp-item-off')) {
                wrapperFront[0].setAttribute('class', 'cbp-item-wrapper cbp-item-on2off');
            }

            if (elBack.is(filterName)) {
                elBack[0].style.left = item.leftNew + 'px';
                elBack[0].style.top = item.topNew + 'px';

                wrapperBack[0].setAttribute('class', 'cbp-item-wrapper cbp-item-off2on');

                elBack.removeClass('cbp-item-off');

                // keep the last item that will be animated to trigger animationend
                animatedEl = wrapperBack;
            } else {
                elBack.addClass('cbp-item-off');
            }
        }

        function transitionend() {
            var i, item;

            t.$obj.removeClass('cbp-transition-active');

            for (i = t.blocksObj.length - 1; i >= 0; i--) {
                item = t.blocksObj[i];

                item.left = item.leftNew;
                item.top = item.topNew;

                item.el[0].style.left = item.left + 'px';
                item.el[0].style.top = item.top + 'px';

            }

            t.filterDeferred.resolve();
        }

        if (!animatedEl) {
            transitionend();
        } else {
            animatedEl.one(CubePortfolio.Private.animationend, function() {
                transitionend();
            });
        }

    };

    AnimationClone.prototype.destroy = function() {
        var p = this.parent;

        p.$obj.removeClass('cbp-animation-' + p.options.animationType);

        p.$ul.removeClass('cbp-wrapper-front').removeAttr('style');

        // remove ul clone from dom
        if (p.$ulClone) {
            p.$ulClone.remove();
        }
    };

    CubePortfolio.Plugins.AnimationClone = function (parent) {

        if (!CubePortfolio.Private.modernBrowser || $.inArray(parent.options.animationType, ['fadeOutTop', 'slideLeft']) < 0) {
            return null;
        }

        return new AnimationClone(parent);
    };

})(jQuery, window, document);

(function($, window, document, undefined) {

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    function AnimationCloneDelay(parent) {
        var t = this;

        t.parent = parent;

        parent._registerEvent('filterBeforeLayout', function() {
            parent.$ulClone[0].style.display = '';
            parent.$obj.addClass('cbp-animation-' + parent.options.animationType);
        }, true);

        parent._registerEvent('initFinish', function() {

            parent.$ulClone = parent.$ul.clone();
            parent.$ulClone[0].style.display = 'none';

            parent.$ulClone.children('.cbp-item').each(function(index, el) {
                el = $(el);

                parent.blocksObj[index].elClone = el;
                parent.blocksObj[index].wrapperClone = el.children();
            });

            parent.$ulClone.insertAfter(parent.$ul);

            parent.wrapperFront = true;
        });

        parent._registerEvent('filterBeforeLayout', function() {
            var i, len, item, wrapper;

            // is $ul here
            if (parent.wrapperFront) {
                parent.$ul.removeClass('cbp-wrapper-front');
                parent.$ulClone.addClass('cbp-wrapper-front');

                parent.wrapperFront = false;

            } else { // is clone
                parent.$ul.addClass('cbp-wrapper-front');
                parent.$ulClone.removeClass('cbp-wrapper-front');

                parent.wrapperFront = true;
            }

        });

        parent._registerEvent('addItemsToDOM', function(items) {
            var newItems = items.clone(),
                lenItems = newItems.length,
                lenObj = parent.blocksObj.length;

            newItems.appendTo(parent.$ulClone);

            newItems.each(function(index, el) {
                el = $(el);
                parent.blocksObj[lenObj + index - lenItems].elClone = el;
                parent.blocksObj[lenObj + index - lenItems].wrapperClone = el.children();

                if (!parent.wrapperFront) {
                    parent.blocksObj[lenObj + index - lenItems].elFront = el;
                }
            });

        });

        parent.filterLayout = t.filterLayout;

    }

    AnimationCloneDelay.prototype.filterLayout = function(filterName) {
        var t = this,
            delayBack = 0,
            delayFront = 0,
            item, i, len, elFront, elBack, wrapperFront, wrapperBack, animatedEl;

        for (i = 0, len = t.blocksObj.length; i < len; i++) {
            item = t.blocksObj[i];

            if (t.wrapperFront) {
                elFront = item.elClone;
                elBack = item.el;
                wrapperFront = item.wrapperClone;
                wrapperBack = item.wrapper;

                // keep track what el is in front
                item.elFront = item.el;
            } else {
                elFront = item.el;
                elBack = item.elClone;
                wrapperFront = item.wrapper;
                wrapperBack = item.wrapperClone;

                // keep track what el is in front
                item.elFront = item.elClone;
            }

            if (!elFront.hasClass('cbp-item-off')) {
                wrapperFront[0].style[CubePortfolio.Private.animationDelay] = (delayFront * 50) + 'ms';
                delayFront++;
                wrapperFront[0].setAttribute('class', 'cbp-item-wrapper cbp-item-on2off');
            }

            if (elBack.is(filterName)) {
                elBack[0].style.left = item.leftNew + 'px';
                elBack[0].style.top = item.topNew + 'px';

                wrapperBack[0].setAttribute('class', 'cbp-item-wrapper cbp-item-off2on');

                wrapperBack[0].style[CubePortfolio.Private.animationDelay] = (delayBack * 50) + 'ms';
                delayBack++;

                elBack.removeClass('cbp-item-off');

                // keep the last item that will be animated to trigger animationend
                animatedEl = wrapperBack;
            } else {
                elBack.addClass('cbp-item-off');
            }
        }

        function transitionend() {
            var i, item;

            for (i = t.blocksObj.length - 1; i >= 0; i--) {
                item = t.blocksObj[i];

                item.left = item.leftNew;
                item.top = item.topNew;

                item.el[0].style.left = item.left + 'px';
                item.el[0].style.top = item.top + 'px';
            }

            t.filterDeferred.resolve();
        }

        if (!animatedEl) {
            transitionend();
        } else {
            animatedEl.one(CubePortfolio.Private.animationend, function() {
                transitionend();
            });
        }

    };

    AnimationCloneDelay.prototype.destroy = function() {
        var p = this.parent;

        p.$obj.removeClass('cbp-animation-' + p.options.animationType);

        p.$ul.removeClass('cbp-wrapper-front').removeAttr('style');

        // remove ul clone from dom
        if (p.$ulClone) {
            p.$ulClone.remove();
        }
    };

    CubePortfolio.Plugins.AnimationCloneDelay = function(parent) {

        if (!CubePortfolio.Private.modernBrowser ||
            $.inArray(parent.options.animationType, ['3dflip', 'flipOutDelay', 'slideDelay', 'rotateSides', 'foldLeft', 'unfold', 'scaleDown', 'frontRow', 'rotateRoom']) < 0) {
            return null;
        }

        return new AnimationCloneDelay(parent);
    };

})(jQuery, window, document);

(function($, window, document, undefined) {

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    function AnimationSequentially(parent) {
        var t = this;

        t.parent = parent;

        parent._registerEvent('filterBeforeLayout', function() {
            parent.$ulClone[0].style.display = '';
            parent.$obj.addClass('cbp-animation-' + parent.options.animationType);
        }, true);

        parent._registerEvent('initFinish', function() {

            parent.$ulClone = parent.$ul.clone();
            parent.$ulClone[0].style.display = 'none';

            parent.$ulClone.children('.cbp-item').each(function(index, el) {
                el = $(el);

                parent.blocksObj[index].elClone = el;
                parent.blocksObj[index].wrapperClone = el.children();
            });

            parent.$ulClone.insertAfter(parent.$ul);

            parent.wrapperFront = true;
        });

        parent._registerEvent('filterBeforeLayout', function() {
            var i, len, item, wrapper;

            parent.$obj.addClass('cbp-transition-active');

            // is $ul here
            if (parent.wrapperFront) {
                parent.$ul.removeClass('cbp-wrapper-front');
                parent.$ulClone.addClass('cbp-wrapper-front');

                parent.wrapperFront = false;

            } else { // is clone
                parent.$ul.addClass('cbp-wrapper-front');
                parent.$ulClone.removeClass('cbp-wrapper-front');

                parent.wrapperFront = true;
            }

        });

        parent._registerEvent('addItemsToDOM', function(items) {
            var newItems = items.clone(),
                lenItems = newItems.length,
                lenObj = parent.blocksObj.length;

            newItems.appendTo(parent.$ulClone);

            newItems.each(function(index, el) {
                el = $(el);
                parent.blocksObj[lenObj + index - lenItems].elClone = el;
                parent.blocksObj[lenObj + index - lenItems].wrapperClone = el.children();

                if (!parent.wrapperFront) {
                    parent.blocksObj[lenObj + index - lenItems].elFront = el;
                }
            });

        });

        parent.filterLayout = t.filterLayout;

    }

    AnimationSequentially.prototype.filterLayout = function(filterName) {
        var t = this,
            delayBack = 0,
            item, i, len, elFront, elBack, wrapperFront, wrapperBack, animatedEl;

        for (i = 0, len = t.blocksObj.length; i < len; i++) {
            item = t.blocksObj[i];

            if (t.wrapperFront) {
                elFront = item.elClone;
                elBack = item.el;
                wrapperFront = item.wrapperClone;
                wrapperBack = item.wrapper;

                // keep track what el is in front
                item.elFront = item.el;
            } else {
                elFront = item.el;
                elBack = item.elClone;
                wrapperFront = item.wrapper;
                wrapperBack = item.wrapperClone;

                // keep track what el is in front
                item.elFront = item.elClone;
            }

            if (!elFront.hasClass('cbp-item-off')) {
                wrapperFront[0].setAttribute('class', 'cbp-item-wrapper cbp-item-on2off');
            }

            if (elBack.is(filterName)) {
                elBack[0].style.left = item.leftNew + 'px';
                elBack[0].style.top = item.topNew + 'px';

                wrapperBack[0].setAttribute('class', 'cbp-item-wrapper cbp-item-off2on');

                wrapperBack[0].style[CubePortfolio.Private.animationDelay] = (delayBack * 60) + 'ms';
                delayBack++;

                elBack.removeClass('cbp-item-off');

                // keep the last item that will be animated to trigger animationend
                animatedEl = wrapperBack;
            } else {
                elBack.addClass('cbp-item-off');
            }
        }

        function transitionend() {
            var i, item;

            t.$obj.removeClass('cbp-transition-active');

            for (i = t.blocksObj.length - 1; i >= 0; i--) {
                item = t.blocksObj[i];

                item.left = item.leftNew;
                item.top = item.topNew;

                item.el[0].style.left = item.left + 'px';
                item.el[0].style.top = item.top + 'px';

                item.wrapper[0].style[CubePortfolio.Private.animationDelay] = '';
                item.wrapperClone[0].style[CubePortfolio.Private.animationDelay] = '';
            }

            t.filterDeferred.resolve();
        }

        if (!animatedEl) {
            transitionend();
        } else {
            animatedEl.one(CubePortfolio.Private.animationend, function() {
                transitionend();
            });
        }

    };

    AnimationSequentially.prototype.destroy = function() {
        var p = this.parent;

        p.$obj.removeClass('cbp-animation-' + p.options.animationType);

        p.$ul.removeClass('cbp-wrapper-front').removeAttr('style');

        // remove ul clone from dom
        if (p.$ulClone) {
            p.$ulClone.remove();
        }
    };

    CubePortfolio.Plugins.AnimationSequentially = function (parent) {

        if (!CubePortfolio.Private.modernBrowser || parent.options.animationType !== 'sequentially') {
            return null;
        }

        return new AnimationSequentially(parent);
    };

})(jQuery, window, document);

(function($, window, document, undefined) {

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    function AnimationWrapper(parent) {
        var t = this;

        t.parent = parent;

        parent._registerEvent('filterBeforeLayout', function() {
            parent.$ulClone[0].style.display = '';
            parent.$obj.addClass('cbp-animation-' + parent.options.animationType);
        }, true);

        parent._registerEvent('initFinish', function() {

            parent.$ulClone = parent.$ul.clone();
            parent.$ulClone[0].style.display = 'none';

            parent.$ulClone.children('.cbp-item').each(function(index, el) {
                el = $(el);

                parent.blocksObj[index].elClone = el;
                parent.blocksObj[index].wrapperClone = el.children();
            });

            parent.$ulClone.insertAfter(parent.$ul);

            parent.wrapperFront = true;
        });

        parent._registerEvent('filterBeforeLayout', function() {
            var i, len, item, wrapper;

            // is $ul here
            if (parent.wrapperFront) {
                parent.$ul.removeClass('cbp-wrapper-front').addClass('cbp-wrapper-back');
                parent.$ulClone.removeClass('cbp-wrapper-back').addClass('cbp-wrapper-front');

                parent.wrapperFront = false;

            } else { // is clone
                parent.$ul.removeClass('cbp-wrapper-back').addClass('cbp-wrapper-front');
                parent.$ulClone.removeClass('cbp-wrapper-front').addClass('cbp-wrapper-back');

                parent.wrapperFront = true;
            }

        });

        parent._registerEvent('addItemsToDOM', function(items) {
            var newItems = items.clone(),
                lenItems = newItems.length,
                lenObj = parent.blocksObj.length;

            newItems.appendTo(parent.$ulClone);

            newItems.each(function(index, el) {
                el = $(el);
                parent.blocksObj[lenObj + index - lenItems].elClone = el;
                parent.blocksObj[lenObj + index - lenItems].wrapperClone = el.children();

                if (!parent.wrapperFront) {
                    parent.blocksObj[lenObj + index - lenItems].elFront = el;
                }
            });

        });

        parent.filterLayout = t.filterLayout;

    }

    AnimationWrapper.prototype.filterLayout = function(filterName) {
        var t = this,
            item, i, len, elBack;

        for (i = 0, len = t.blocksObj.length; i < len; i++) {
            item = t.blocksObj[i];

            if (t.wrapperFront) {
                elBack = item.el;

                // keep track what el is in front
                item.elFront = item.el;
            } else {
                elBack = item.elClone;

                // keep track what el is in front
                item.elFront = item.elClone;
            }

            if (elBack.is(filterName)) {
                elBack[0].style.left = item.leftNew + 'px';
                elBack[0].style.top = item.topNew + 'px';

                elBack.removeClass('cbp-item-off');
            } else {
                elBack.addClass('cbp-item-off');
            }
        }


        t.$ul.one(CubePortfolio.Private.animationend, function() {
            var i, item;

            for (i = t.blocksObj.length - 1; i >= 0; i--) {
                item = t.blocksObj[i];

                item.left = item.leftNew;
                item.top = item.topNew;

                item.el[0].style.left = item.left + 'px';
                item.el[0].style.top = item.top + 'px';
            }

            t.filterDeferred.resolve();
        });

    };

    AnimationWrapper.prototype.destroy = function() {
        var p = this.parent;

        p.$obj.removeClass('cbp-animation-' + p.options.animationType);

        p.$ul.removeClass('cbp-wrapper-front').removeAttr('style');

        // remove ul clone from dom
        if (p.$ulClone) {
            p.$ulClone.remove();
        }
    };

    CubePortfolio.Plugins.AnimationWrapper = function(parent) {

        if (!CubePortfolio.Private.modernBrowser ||
            $.inArray(parent.options.animationType, ['bounceLeft', 'bounceBottom', 'bounceTop', 'moveLeft']) < 0) {
            return null;
        }

        return new AnimationWrapper(parent);
    };

})(jQuery, window, document);

(function($, window, document, undefined) {

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    function BottomToTop(parent) {

        // skip next event from core
        parent._skipNextEvent('delayFrame');

        parent._registerEvent('initEndWrite', function() {

            $.each(parent.blocksOn, function(index, item) {
                item.el[0].style[CubePortfolio.Private.animationDelay] = (index * parent.options.displayTypeSpeed) + 'ms';
            });

            parent.$obj.addClass('cbp-displayType-bottomToTop');

            // get last element
            parent.blocksOn.slice(-1)[0].el.one(CubePortfolio.Private.animationend, function() {
                parent.$obj.removeClass('cbp-displayType-bottomToTop');

                $.each(parent.blocksOn, function(index, item) {
                    item.el[0].style[CubePortfolio.Private.animationDelay] = '';
                });

                // trigger event after the animation is finished
                parent._triggerEvent('delayFrame');
            });

        }, true);

    }

    CubePortfolio.Plugins.BottomToTop = function (parent) {

        if (!CubePortfolio.Private.modernBrowser || parent.options.displayType !== 'bottomToTop') {
            return null;
        }

        return new BottomToTop(parent);
    };

})(jQuery, window, document);

(function($, window, document, undefined) {

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    function FadeInToTop(parent) {

        // skip next event from core
        parent._skipNextEvent('delayFrame');

        parent._registerEvent('initEndWrite', function() {
            parent.obj.style[CubePortfolio.Private.animationDuration] = parent.options.displayTypeSpeed + 'ms';
            parent.$obj.addClass('cbp-displayType-fadeInToTop');

            parent.$obj.one(CubePortfolio.Private.animationend, function() {
                parent.$obj.removeClass('cbp-displayType-fadeInToTop');

                parent.obj.style[CubePortfolio.Private.animationDuration] = '';

                // trigger event after the animation is finished
                parent._triggerEvent('delayFrame');
            });

        }, true);

    }

    CubePortfolio.Plugins.FadeInToTop = function (parent) {

        if (!CubePortfolio.Private.modernBrowser || parent.options.displayType !== 'fadeInToTop') {
            return null;
        }

        return new FadeInToTop(parent);
    };

})(jQuery, window, document);

(function($, window, document, undefined) {

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    function LazyLoading(parent) {

        // skip next event from core
        parent._skipNextEvent('delayFrame');

        parent._registerEvent('initEndWrite', function() {
            parent.obj.style[CubePortfolio.Private.animationDuration] = parent.options.displayTypeSpeed + 'ms';
            parent.$obj.addClass('cbp-displayType-lazyLoading');

            parent.$obj.one(CubePortfolio.Private.animationend, function() {
                parent.$obj.removeClass('cbp-displayType-lazyLoading');

                parent.obj.style[CubePortfolio.Private.animationDuration] = '';

                // trigger event after the animation is finished
                parent._triggerEvent('delayFrame');
            });

        }, true);

    }

    CubePortfolio.Plugins.LazyLoading = function (parent) {

        if (!CubePortfolio.Private.modernBrowser || (parent.options.displayType !== 'lazyLoading' && parent.options.displayType !== 'fadeIn')) {
            return null;
        }

        return new LazyLoading(parent);
    };

})(jQuery, window, document);

(function($, window, document, undefined) {

    var CubePortfolio = $.fn.cubeportfolio.Constructor;

    function DisplaySequentially(parent) {

        // skip next event from core
        parent._skipNextEvent('delayFrame');

        parent._registerEvent('initEndWrite', function() {

            $.each(parent.blocksOn, function(index, item) {
                item.el[0].style[CubePortfolio.Private.animationDelay] = (index * parent.options.displayTypeSpeed) + 'ms';
            });

            parent.$obj.addClass('cbp-displayType-sequentially');

            // get last element
            parent.blocksOn.slice(-1)[0].el.one(CubePortfolio.Private.animationend, function() {
                parent.$obj.removeClass('cbp-displayType-sequentially');

                $.each(parent.blocksOn, function(index, item) {
                    item.el[0].style[CubePortfolio.Private.animationDelay] = '';
                });

                // trigger event after the animation is finished
                parent._triggerEvent('delayFrame');
            });

        }, true);

    }

    CubePortfolio.Plugins.DisplaySequentially = function (parent) {

        if (!CubePortfolio.Private.modernBrowser || parent.options.displayType !== 'sequentially') {
            return null;
        }

        return new DisplaySequentially(parent);
    };

})(jQuery, window, document);
