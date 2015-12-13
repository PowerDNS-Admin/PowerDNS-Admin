/**************************************************************************
 * jquery.themepunch.revolution.js - jQuery Plugin for Revolution Slider
 * @version: 4.6.4 (26.11.2014)
 * @requires jQuery v1.7 or later (tested on 1.9)
 * @author ThemePunch
**************************************************************************/


(function(jQuery,undefined){




	////////////////////////////////////////
	// THE REVOLUTION PLUGIN STARTS HERE //
	///////////////////////////////////////

	jQuery.fn.extend({

		// OUR PLUGIN HERE :)
		revolution: function(options) {



				////////////////////////////////
				// SET DEFAULT VALUES OF ITEM //
				////////////////////////////////
				var defaults = {
					delay:9000,
					startheight:500,
					startwidth:960,
					fullScreenAlignForce:"off",
					autoHeight:"off",
					hideTimerBar:"off",
					hideThumbs:200,
					hideNavDelayOnMobile:1500,

					thumbWidth:100,							// Thumb With and Height and Amount (only if navigation Tyope set to thumb !)
					thumbHeight:50,
					thumbAmount:3,

					navigationType:"bullet",				// bullet, thumb, none
					navigationArrows:"solo",				// nextto, solo, none
					navigationInGrid:"off",					// on/off

					hideThumbsOnMobile:"off",
					hideBulletsOnMobile:"off",
					hideArrowsOnMobile:"off",
					hideThumbsUnderResoluition:0,

					navigationStyle:"round",				// round,square,navbar,round-old,square-old,navbar-old, or any from the list in the docu (choose between 50+ different item),

					navigationHAlign:"center",				// Vertical Align top,center,bottom
					navigationVAlign:"bottom",				// Horizontal Align left,center,right
					navigationHOffset:0,
					navigationVOffset:20,

					soloArrowLeftHalign:"left",
					soloArrowLeftValign:"center",
					soloArrowLeftHOffset:20,
					soloArrowLeftVOffset:0,

					soloArrowRightHalign:"right",
					soloArrowRightValign:"center",
					soloArrowRightHOffset:20,
					soloArrowRightVOffset:0,

					keyboardNavigation:"on",

					touchenabled:"on",						// Enable Swipe Function : on/off
					onHoverStop:"on",						// Stop Banner Timet at Hover on Slide on/off


					stopAtSlide:-1,							// Stop Timer if Slide "x" has been Reached. If stopAfterLoops set to 0, then it stops already in the first Loop at slide X which defined. -1 means do not stop at any slide. stopAfterLoops has no sinn in this case.
					stopAfterLoops:-1,						// Stop Timer if All slides has been played "x" times. IT will stop at THe slide which is defined via stopAtSlide:x, if set to -1 slide never stop automatic

					hideCaptionAtLimit:0,					// It Defines if a caption should be shown under a Screen Resolution ( Basod on The Width of Browser)
					hideAllCaptionAtLimit:0,				// Hide all The Captions if Width of Browser is less then this value
					hideSliderAtLimit:0,					// Hide the whole slider, and stop also functions if Width of Browser is less than this value

					shadow:0,								//0 = no Shadow, 1,2,3 = 3 Different Art of Shadows  (No Shadow in Fullwidth Version !)
					fullWidth:"off",						// Turns On or Off the Fullwidth Image Centering in FullWidth Modus
					fullScreen:"off",
					minFullScreenHeight:0,					// The Minimum FullScreen Height
					fullScreenOffsetContainer:"",			// Size for FullScreen Slider minimising Calculated on the Container sizes
					fullScreenOffset:"0",					// Size for FullScreen Slider minimising
					dottedOverlay:"none",					//twoxtwo, threexthree, twoxtwowhite, threexthreewhite

					forceFullWidth:"off",						// Force The FullWidth

					spinner:"spinner0",

					swipe_treshold : 75,					// The number of pixels that the user must move their finger by before it is considered a swipe.
					swipe_min_touches : 1,					// Min Finger (touch) used for swipe
					drag_block_vertical:false,				// Prevent Vertical Scroll during Swipe
					isJoomla:false,
					parallax:"off",
					parallaxLevels: [10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85],
					parallaxBgFreeze: "off",
					parallaxOpacity:"on",
					parallaxDisableOnMobile:"off",
					panZoomDisableOnMobile:"off",
					simplifyAll:"on",
					minHeight:0,
					nextSlideOnWindowFocus:"off",

					startDelay:0		// Delay before the first Animation starts.


				};

					options = jQuery.extend({}, defaults, options);

					return this.each(function() {


						// REPORT SOME IMPORTAN INFORMATION ABOUT THE SLIDER
						if (window.tplogs==true)
						 try{
								console.groupCollapsed("Slider Revolution 4.6.3 Initialisation on "+jQuery(this).attr('id'));
								console.groupCollapsed("Used Options:");
								console.info(options);
								console.groupEnd();
								console.groupCollapsed("Tween Engine:")
							} catch(e) {}

						// CHECK IF TweenLite IS LOADED AT ALL
						if (punchgs.TweenLite==undefined) {
						   if (window.tplogs==true)
						    try{ console.error("GreenSock Engine Does not Exist!");
						    } catch(e) {}
							return false;
						}

						punchgs.force3D = true;

						if (window.tplogs==true)
							try{ console.info("GreenSock Engine Version in Slider Revolution:"+punchgs.TweenLite.version);
							} catch(e) {

							}

						if (options.simplifyAll=="on") {

						} else {
							punchgs.TweenLite.lagSmoothing(1000,16);
							punchgs.force3D = "true";
						}

						if (window.tplogs==true)
							try{
								console.groupEnd();
								console.groupEnd();
							} catch(e) {}


						initSlider(jQuery(this),options)


					})
				},


		// METHODE PAUSE
		revscroll: function(oy) {
					return this.each(function() {
						var container=jQuery(this);
						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0)
							jQuery('body,html').animate({scrollTop:(container.offset().top+(container.find('>ul >li').height())-oy)+"px"},{duration:400});
					})
				},

		// METHODE PAUSE
		revredraw: function(oy) {
					return this.each(function() {
						var container=jQuery(this);
						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0) {
							var bt = container.parent().find('.tp-bannertimer');
							var opt = bt.data('opt');
							containerResized(container,opt);
						}
					})
				},
		// METHODE PAUSE
		revkill: function(oy) {

						var self = this,
							container=jQuery(this);

						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0) {

							container.data('conthover',1);
							container.data('conthover-changed',1);
							container.trigger('revolution.slide.onpause');
							var bt = container.parent().find('.tp-bannertimer');
							var opt = bt.data('opt');
							opt.bannertimeronpause = true;
							container.trigger('stoptimer');

							punchgs.TweenLite.killTweensOf(container.find('*'),false);
							punchgs.TweenLite.killTweensOf(container,false);
							container.unbind('hover, mouseover, mouseenter,mouseleave, resize');
							var resizid = "resize.revslider-"+container.attr('id');
							jQuery(window).off(resizid);
							container.find('*').each(function() {
									var el = jQuery(this);

									el.unbind('on, hover, mouseenter,mouseleave,mouseover, resize,restarttimer, stoptimer');
									el.off('on, hover, mouseenter,mouseleave,mouseover, resize');
									el.data('mySplitText',null);
									el.data('ctl',null);
									if (el.data('tween')!=undefined)
										el.data('tween').kill();
									if (el.data('kenburn')!=undefined)
										el.data('kenburn').kill();
									el.remove();
									el.empty();
									el=null;
							})


							punchgs.TweenLite.killTweensOf(container.find('*'),false);
							punchgs.TweenLite.killTweensOf(container,false);
							bt.remove();
							try{container.closest('.forcefullwidth_wrapper_tp_banner').remove();} catch(e) {}
							try{container.closest('.rev_slider_wrapper').remove()} catch(e) {}
							try{container.remove();} catch(e) {}
							container.empty();
							container.html();
							container = null;

							opt = null;
							delete(self.container);
							delete(self.opt);

							return true;
						} else {
							return false;
						}


				},

		// METHODE PAUSE
		revpause: function(options) {

					return this.each(function() {
						var container=jQuery(this);
						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0) {
							container.data('conthover',1);
							container.data('conthover-changed',1);
							container.trigger('revolution.slide.onpause');
							var bt = container.parent().find('.tp-bannertimer');
							var opt = bt.data('opt');
							opt.bannertimeronpause = true;
							container.trigger('stoptimer');
						}
					})


				},

		// METHODE RESUME
		revresume: function(options) {
					return this.each(function() {
						var container=jQuery(this);
						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0) {
							container.data('conthover',0);
							container.data('conthover-changed',1);
							container.trigger('revolution.slide.onresume');
							var bt = container.parent().find('.tp-bannertimer');
							var opt = bt.data('opt');
							opt.bannertimeronpause = false;
							container.trigger('starttimer');
						}
					})

				},

		// METHODE NEXT
		revnext: function(options) {
					return this.each(function() {

						// CATCH THE CONTAINER
						var container=jQuery(this);
						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0)
							container.parent().find('.tp-rightarrow').click();


					})

				},

		// METHODE RESUME
		revprev: function(options) {
					return this.each(function() {
						// CATCH THE CONTAINER
						var container=jQuery(this);
						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0)
							container.parent().find('.tp-leftarrow').click();
					})

				},

		// METHODE LENGTH
		revmaxslide: function(options) {
						// CATCH THE CONTAINER
						return jQuery(this).find('>ul:first-child >li').length;
				},


		// METHODE CURRENT
		revcurrentslide: function(options) {
						// CATCH THE CONTAINER
						var container=jQuery(this);
						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0) {
							var bt = container.parent().find('.tp-bannertimer');
							var opt = bt.data('opt');
							return opt.act;
						}
				},

		// METHODE CURRENT
		revlastslide: function(options) {
						// CATCH THE CONTAINER
						var container=jQuery(this);
						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0) {
							var bt = container.parent().find('.tp-bannertimer');
							var opt = bt.data('opt');
							return opt.lastslide;
						}
				},


		// METHODE JUMP TO SLIDE
		revshowslide: function(slide) {
					return this.each(function() {
						// CATCH THE CONTAINER
						var container=jQuery(this);
						if (container!=undefined && container.length>0 && jQuery('body').find('#'+container.attr('id')).length>0) {
							container.data('showus',slide);
							container.parent().find('.tp-rightarrow').click();
						}
					})

				}


})
		/*******************************************
			-	IS IOS VERSION OLDER THAN 5 ??	-
		*******************************************/

		function iOSVersion() {
			var oldios = false;
			if((navigator.userAgent.match(/iPhone/i)) || (navigator.userAgent.match(/iPod/i)) || (navigator.userAgent.match(/iPad/i))) {
		        if (navigator.userAgent.match(/OS 4_\d like Mac OS X/i)) {
		        	oldios = true;
				}
		    } else {
				   oldios = false;
		    }
			return oldios;
		}

		function initSlider(container,opt) {
						if (container==undefined) return false;

						if (container.data('aimg')!=undefined) {
							if ((container.data('aie8')=="enabled" && isIE(8)) || (container.data('amobile')=="enabled" && is_mobile()))
								container.html('<img class="tp-slider-alternative-image" src="'+container.data("aimg")+'">');
						}
						// PREPARE FALL BACK SETTINGS
						if (opt.navigationStyle=="preview1" ||  opt.navigationStyle=="preview3" || opt.navigationStyle=="preview4") {
									opt.soloArrowLeftHalign="left";
									opt.soloArrowLeftValign="center";
									opt.soloArrowLeftHOffset=0;
									opt.soloArrowLeftVOffset=0;
									opt.soloArrowRightHalign="right";
									opt.soloArrowRightValign="center";
									opt.soloArrowRightHOffset=0;
									opt.soloArrowRightVOffset=0;
									opt.navigationArrows="solo";
						}


						// SIMPLIFY ANIMATIONS ON OLD IOS AND IE8 IF NEEDED
						if (opt.simplifyAll=="on" && (isIE(8) || iOSVersion())) {
							container.find('.tp-caption').each(function() {
								var tc = jQuery(this);
								tc.removeClass("customin").removeClass("customout").addClass("fadein").addClass("fadeout");
								tc.data('splitin',"");
								tc.data('speed',400);
							})
							container.find('>ul>li').each(function() {
								var li= jQuery(this);
								li.data('transition',"fade");
								li.data('masterspeed',500);
								li.data('slotamount',1);
								var img = li.find('>img').first();
								img.data('kenburns',"off");
							});
						}





						opt.desktop = !navigator.userAgent.match(/(iPhone|iPod|iPad|Android|BlackBerry|BB10|mobi|tablet|opera mini|nexus 7)/i);

						if (opt.fullWidth!="on" && opt.fullScreen!="on") opt.autoHeight = "off";
						if (opt.fullScreen=="on") opt.autoHeight = "on";
						if (opt.fullWidth!="on" && opt.fullScreen!="on") forceFulWidth="off";

						if (opt.fullWidth=="on" && opt.autoHeight=="off")
							container.css({maxHeight:opt.startheight+"px"});

						if (is_mobile() && opt.hideThumbsOnMobile=="on" && opt.navigationType=="thumb")
						   opt.navigationType = "none"

						if (is_mobile() && opt.hideBulletsOnMobile=="on" && opt.navigationType=="bullet")
						   opt.navigationType = "none"

						if (is_mobile() && opt.hideBulletsOnMobile=="on" && opt.navigationType=="both")
						   opt.navigationType = "none"

						if (is_mobile() && opt.hideArrowsOnMobile=="on")
						   opt.navigationArrows = "none"

						if (opt.forceFullWidth=="on" && container.closest('.forcefullwidth_wrapper_tp_banner').length==0) {

							var loff = container.parent().offset().left;
							var mb = container.parent().css('marginBottom');
							var mt = container.parent().css('marginTop');
							if (mb==undefined) mb=0;
							if (mt==undefined) mt=0;

							container.parent().wrap('<div style="position:relative;width:100%;height:auto;margin-top:'+mt+';margin-bottom:'+mb+'" class="forcefullwidth_wrapper_tp_banner"></div>');
							container.closest('.forcefullwidth_wrapper_tp_banner').append('<div class="tp-fullwidth-forcer" style="width:100%;height:'+container.height()+'px"></div>');
							container.css({'backgroundColor':container.parent().css('backgroundColor'),'backgroundImage':container.parent().css('backgroundImage')});
							//container.parent().css({'position':'absolute','width':jQuery(window).width()});
							container.parent().css({'left':(0-loff)+"px",position:'absolute','width':jQuery(window).width()});
							opt.width=jQuery(window).width();
						}

						// HIDE THUMBS UNDER RESOLUTION
						try{
							if (opt.hideThumbsUnderResolution>jQuery(window).width() && opt.hideThumbsUnderResolution!=0) {
								container.parent().find('.tp-bullets.tp-thumbs').css({display:"none"});
							} else {
								container.parent().find('.tp-bullets.tp-thumbs').css({display:"block"});
							}
						} catch(e) {}

						if (!container.hasClass("revslider-initialised")) {

									container.addClass("revslider-initialised");
									if (container.attr('id')==undefined) container.attr('id',"revslider-"+Math.round(Math.random()*1000+5));

									// CHECK IF FIREFOX 13 IS ON WAY.. IT HAS A STRANGE BUG, CSS ANIMATE SHOULD NOT BE USED



									opt.firefox13 = false;
									opt.ie = !jQuery.support.opacity;
									opt.ie9 = (document.documentMode == 9);

									opt.origcd=opt.delay;

									// CHECK THE jQUERY VERSION
									var version = jQuery.fn.jquery.split('.'),
										versionTop = parseFloat(version[0]),
										versionMinor = parseFloat(version[1]),
										versionIncrement = parseFloat(version[2] || '0');

									if (versionTop==1 && versionMinor < 7) {
										container.html('<div style="text-align:center; padding:40px 0px; font-size:20px; color:#992222;"> The Current Version of jQuery:'+version+' <br>Please update your jQuery Version to min. 1.7 in Case you wish to use the Revolution Slider Plugin</div>');
									}

									if (versionTop>1) opt.ie=false;


									// Delegate .transition() calls to .animate()
									// if the browser can't do CSS transitions.
									if (!jQuery.support.transition)
										jQuery.fn.transition = jQuery.fn.animate;

									// CATCH THE CONTAINER


									 // LOAD THE YOUTUBE API IF NECESSARY

									container.find('.caption').each(function() { jQuery(this).addClass('tp-caption')});

									if (is_mobile()) {
										container.find('.tp-caption').each(function() {
											var nextcaption = jQuery(this);
											if (nextcaption.data('autoplayonlyfirsttime') == true || nextcaption.data('autoplayonlyfirsttime')=="true")
													nextcaption.data('autoplayonlyfirsttime',"false");
											if (nextcaption.data('autoplay')==true || nextcaption.data('autoplay')=="true")
												 nextcaption.data('autoplay',false);

										})
									}


									var addedyt=0;
									var addedvim=0;
									var addedvid=0;
									var httpprefix = "http";

									if (location.protocol === 'https:') {
											httpprefix = "https";
									}
									container.find('.tp-caption').each(function(i) {
										// IF SRC EXIST, RESET SRC'S since WE DONT NEED THEM !!

										try {

												if ((jQuery(this).data('ytid')!=undefined  || jQuery(this).find('iframe').attr('src').toLowerCase().indexOf('youtube')>0) && addedyt==0) {
													addedyt=1;
													var s = document.createElement("script");
													var httpprefix2 = "https";
													s.src = httpprefix2+"://www.youtube.com/iframe_api"; /* Load Player API*/

													var before = document.getElementsByTagName("script")[0];
													var loadit = true;
													jQuery('head').find('*').each(function(){
														if (jQuery(this).attr('src') == httpprefix2+"://www.youtube.com/iframe_api")
														   loadit = false;
													});
													if (loadit) {
														before.parentNode.insertBefore(s, before);


													}
												}
											} catch(e) {}

										try{
											   if ((jQuery(this).data('vimeoid')!=undefined || jQuery(this).find('iframe').attr('src').toLowerCase().indexOf('vimeo')>0) && addedvim==0) {
													addedvim=1;
													var f = document.createElement("script");
													f.src = httpprefix+"://a.vimeocdn.com/js/froogaloop2.min.js"; /* Load Player API*/
													var before = document.getElementsByTagName("script")[0];

													var loadit = true;
													jQuery('head').find('*').each(function(){
														if (jQuery(this).attr('src') == httpprefix+"://a.vimeocdn.com/js/froogaloop2.min.js")
														   loadit = false;
													});
													if (loadit)
														before.parentNode.insertBefore(f, before);
												}
											} catch(e) {}

										try{
											if ((jQuery(this).data('videomp4')!=undefined || jQuery(this).data('videowebm')!=undefined))  {

											}
										} catch(e) {}
									});




									// REMOVE ANY VIDEO JS SETTINGS OF THE VIDEO  IF NEEDED
									container.find('.tp-caption video').each(function(i) {
										jQuery(this).removeClass("video-js").removeClass("vjs-default-skin");
										jQuery(this).attr("preload","");
										jQuery(this).css({display:"none"});
									});

									container.find('>ul:first-child >li').each(function() {
											var t = jQuery(this);
											t.data('origindex',t.index());
										})

									// SHUFFLE MODE
									if (opt.shuffle=="on") {
										var fsa = new Object,
											fli = container.find('>ul:first-child >li:first-child')

										fsa.fstransition = fli.data('fstransition');
										fsa.fsmasterspeed = fli.data('fsmasterspeed');
										fsa.fsslotamount = fli.data('fsslotamount');



										for (var u=0;u<container.find('>ul:first-child >li').length;u++) {
											var it = Math.round(Math.random()*container.find('>ul:first-child >li').length);
											container.find('>ul:first-child >li:eq('+it+')').prependTo(container.find('>ul:first-child'));
										}

										var newfli = container.find('>ul:first-child >li:first-child');
										 newfli.data('fstransition',fsa.fstransition);
										 newfli.data('fsmasterspeed',fsa.fsmasterspeed);
										 newfli.data('fsslotamount',fsa.fsslotamount);
									}


									// CREATE SOME DEFAULT OPTIONS FOR LATER
									opt.slots=4;
									opt.act=-1;
									opt.next=0;

									// IF START SLIDE IS SET
									if (opt.startWithSlide !=undefined) opt.next=opt.startWithSlide;

									// IF DEEPLINK HAS BEEN SET
									var deeplink = getUrlVars("#")[0];
									if (deeplink.length<9) {
										if (deeplink.split('slide').length>1) {
											var dslide=parseInt(deeplink.split('slide')[1],0);
											if (dslide<1) dslide=1;
											if (dslide>container.find('>ul:first >li').length) dslide=container.find('>ul:first >li').length;
											opt.next=dslide-1;
										}
									}


									opt.firststart=1;

									// BASIC OFFSET POSITIONS OF THE BULLETS
									if (opt.navigationHOffset==undefined) opt.navOffsetHorizontal=0;
									if (opt.navigationVOffset==undefined) opt.navOffsetVertical=0;



									container.append('<div class="tp-loader '+opt.spinner+'">'+
												  		'<div class="dot1"></div>'+
												  	    '<div class="dot2"></div>'+
												  	    '<div class="bounce1"></div>'+
														'<div class="bounce2"></div>'+
														'<div class="bounce3"></div>'+
													 '</div>');

									// RESET THE TIMER
									if (container.find('.tp-bannertimer').length==0) container.append('<div class="tp-bannertimer" style="visibility:hidden"></div>');
									var bt=container.find('.tp-bannertimer');
									if (bt.length>0) {
										bt.css({'width':'0%'});
									};


									// WE NEED TO ADD A BASIC CLASS FOR SETTINGS.CSS
									container.addClass("tp-simpleresponsive");
									opt.container=container;

									//if (container.height()==0) container.height(opt.startheight);

									// AMOUNT OF THE SLIDES
									opt.slideamount = container.find('>ul:first >li').length;


									// A BASIC GRID MUST BE DEFINED. IF NO DEFAULT GRID EXIST THAN WE NEED A DEFAULT VALUE, ACTUAL SIZE OF CONAINER
									if (container.height()==0) container.height(opt.startheight);
									if (opt.startwidth==undefined || opt.startwidth==0) opt.startwidth=container.width();
									if (opt.startheight==undefined || opt.startheight==0) opt.startheight=container.height();

									// OPT WIDTH && HEIGHT SHOULD BE SET
									opt.width=container.width();
									opt.height=container.height();


									// DEFAULT DEPENDECIES
									opt.bw= opt.startwidth / container.width();
									opt.bh = opt.startheight / container.height();

									// IF THE ITEM ALREADY IN A RESIZED FORM
									if (opt.width!=opt.startwidth) {

										opt.height = Math.round(opt.startheight * (opt.width/opt.startwidth));

										container.height(opt.height);

									}

									// LETS SEE IF THERE IS ANY SHADOW
									if (opt.shadow!=0) {
										container.parent().append('<div class="tp-bannershadow tp-shadow'+opt.shadow+'"></div>');
										var loff=0;
										if (opt.forceFullWidth=="on")
													loff = 0-opt.container.parent().offset().left;
										container.parent().find('.tp-bannershadow').css({'width':opt.width,'left':loff});
									}


									container.find('ul').css({'display':'none'});

									var fliparent = container;


									// PREPARE THE SLIDES
									container.find('ul').css({'display':'block'});
									prepareSlides(container,opt);
									if (opt.parallax!="off") checkForParallax(container,opt);

									// CREATE BULLETS
									if (opt.slideamount >1) createBullets(container,opt);

									if (opt.slideamount >1 && opt.navigationType=="thumb") createThumbs(container,opt);
									if (opt.slideamount >1) createArrows(container,opt);
									if (opt.keyboardNavigation=="on") createKeyboard(container,opt);


									swipeAction(container,opt);


									if (opt.hideThumbs>0) hideThumbs(container,opt);
									setTimeout(function() {
										swapSlide(container,opt);
									},opt.startDelay);
									opt.startDelay=0;
									// START COUNTDOWN
									if (opt.slideamount >1) countDown(container,opt);
									setTimeout(function() {
										container.trigger('revolution.slide.onloaded');
									},500);



									/******************************
										-	FULLSCREEN CHANGE	-
									********************************/
									// FULLSCREEN MODE TESTING
									jQuery("body").data('rs-fullScreenMode',false);
									jQuery(window).on ('mozfullscreenchange webkitfullscreenchange fullscreenchange',function(){
									     jQuery("body").data('rs-fullScreenMode',!jQuery("body").data('rs-fullScreenMode'));
									     if (jQuery("body").data('rs-fullScreenMode')) {
										     setTimeout(function() {
										     	jQuery(window).trigger("resize");

										     },200);
									     }
									})


									var resizid = "resize.revslider-"+container.attr('id');

									// IF RESIZED, NEED TO STOP ACTUAL TRANSITION AND RESIZE ACTUAL IMAGES
									jQuery(window).on(resizid,function() {
										if (container==undefined) return false;
										if (jQuery('body').find(container)!=0)
											if (opt.forceFullWidth=="on" ) {

												var loff = opt.container.closest('.forcefullwidth_wrapper_tp_banner').offset().left;
												//opt.container.parent().css({'width':jQuery(window).width()});
												opt.container.parent().css({'left':(0-loff)+"px",'width':jQuery(window).width()});
											}

											if (container.outerWidth(true)!=opt.width || container.is(":hidden")) {
													containerResized(container,opt);
											}




									});

									// HIDE THUMBS UNDER SIZE...
									try{
										if (opt.hideThumbsUnderResoluition!=0 && opt.navigationType=="thumb") {
											if (opt.hideThumbsUnderResoluition>jQuery(window).width())
												jQuery('.tp-bullets').css({display:"none"});
											 else
											 	jQuery('.tp-bullets').css({display:"block"});
										}
									} catch(e) {}



									// CHECK IF THE CAPTION IS A "SCROLL ME TO POSITION" CAPTION IS
									//if (opt.fullScreen=="on") {
										container.find('.tp-scrollbelowslider').on('click',function() {
												var off=0;
												try{
												 	off = jQuery('body').find(opt.fullScreenOffsetContainer).height();
												 } catch(e) {}
												try{
												 	off = off - parseInt(jQuery(this).data('scrolloffset'),0);
												 } catch(e) {}


												jQuery('body,html').animate(
													{scrollTop:(container.offset().top+(container.find('>ul >li').height())-off)+"px"},{duration:400});
											});
									//}


									// FIRST TIME STOP/START HIDE / SHOW SLIDER
									//REMOVE AND SHOW SLIDER ON DEMAND
									var contpar= container.parent();
									if (jQuery(window).width()<opt.hideSliderAtLimit) {
										container.trigger('stoptimer');
										if (contpar.css('display')!="none")
											contpar.data('olddisplay',contpar.css('display'));
										contpar.css({display:"none"});
									}

									tabBlurringCheck(container,opt);

						}

	}



/******************************
	-	MODULES	-
********************************/


		/////////////////////////////////////////
		// main visibility API function
		// check if current tab is active or not
		var vis = (function(){
		    var stateKey,
		        eventKey,
		        keys = {
		                hidden: "visibilitychange",
		                webkitHidden: "webkitvisibilitychange",
		                mozHidden: "mozvisibilitychange",
		                msHidden: "msvisibilitychange"
		    };
		    for (stateKey in keys) {
		        if (stateKey in document) {
		            eventKey = keys[stateKey];
		            break;
		        }
		    }
		    return function(c) {
		        if (c) document.addEventListener(eventKey, c);
		        return !document[stateKey];
		    }
		})();

		var tabBlurringCheck = function(container,opt) {

			var notIE = (document.documentMode === undefined),
			    isChromium = window.chrome;

			if (notIE && !isChromium) {

			    // checks for Firefox and other  NON IE Chrome versions
			    jQuery(window).on("focusin", function () {
					if (container==undefined) return false;

			        setTimeout(function(){
			            // TAB IS ACTIVE, WE CAN START ANY PART OF THE SLIDER
			            if (opt.nextSlideOnWindowFocus=="on") container.revnext();
			            container.revredraw();
			        },300);

			    }).on("focusout", function () {
					// TAB IS NOT ACTIVE, WE CAN STOP ANY PART OF THE SLIDER
			    });

			} else {

			    // checks for IE and Chromium versions
			    if (window.addEventListener) {

			        // bind focus event
			        window.addEventListener("focus", function (event) {
						if (container==undefined) return false;
			            setTimeout(function(){
			                 // TAB IS ACTIVE, WE CAN START ANY PART OF THE SLIDER
				            if (opt.nextSlideOnWindowFocus=="on") container.revnext();
							container.revredraw();
			            },300);

			        }, false);

			        // bind blur event
			        window.addEventListener("blur", function (event) {
						// TAB IS NOT ACTIVE, WE CAN STOP ANY PART OF THE SLIDER
			        }, false);

			    } else {

			        // bind focus event
			        window.attachEvent("focus", function (event) {

			            setTimeout(function(){
							if (container==undefined) return false;
							// TAB IS ACTIVE, WE CAN START ANY PART OF THE SLIDER
				            if (opt.nextSlideOnWindowFocus=="on") container.revnext();
							container.revredraw();
				         },300);

			        });

			        // bind focus event
			        window.attachEvent("blur", function (event) {
						// TAB IS NOT ACTIVE, WE CAN STOP ANY PART OF THE SLIDER
			        });
			    }
			}
		}

		///////////////////////////
		// GET THE URL PARAMETER //
		///////////////////////////
		var getUrlVars = function (hashdivider)
			{
				var vars = [], hash;
				var hashes = window.location.href.slice(window.location.href.indexOf(hashdivider) + 1).split('_');
				for(var i = 0; i < hashes.length; i++)
				{
					hashes[i] = hashes[i].replace('%3D',"=");
					hash = hashes[i].split('=');
					vars.push(hash[0]);
					vars[hash[0]] = hash[1];
				}
				return vars;
			}

		//////////////////////////
		//	CONTAINER RESIZED	//
		/////////////////////////
		var containerResized = function (container,opt) {

			if (container==undefined) return false;
			// HIDE THUMBS UNDER SIZE...
			try{
				if (opt.hideThumbsUnderResoluition!=0 && opt.navigationType=="thumb") {
					if (opt.hideThumbsUnderResoluition>jQuery(window).width())
						jQuery('.tp-bullets').css({display:"none"});
					 else
					 	jQuery('.tp-bullets').css({display:"block"});
				}
			} catch(e) {}



			container.find('.defaultimg').each(function(i) {
					setSize(jQuery(this),opt);
			});


			//REMOVE AND SHOW SLIDER ON DEMAND
			var contpar= container.parent();
			if (jQuery(window).width()<opt.hideSliderAtLimit) {
				container.trigger('stoptimer');
				if (contpar.css('display')!="none")
					contpar.data('olddisplay',contpar.css('display'));
				contpar.css({display:"none"});

			} else {

				if (container.is(":hidden")) {
					if (contpar.data('olddisplay')!=undefined && contpar.data('olddisplay')!="undefined" && contpar.data('olddisplay') != "none")
						contpar.css({display:contpar.data('olddisplay')});
					else
						contpar.css({display:"block"});
					container.trigger('restarttimer');
					setTimeout(function() {
						containerResized(container,opt);
					},150)
				}
			}


			var loff=0;
			if (opt.forceFullWidth=="on")
						loff = 0-opt.container.parent().offset().left;
			try{
				container.parent().find('.tp-bannershadow').css({'width':opt.width,'left':loff});
			} catch(e) {}

			var actsh = container.find('>ul >li:eq('+opt.act+') .slotholder');
			var nextsh = container.find('>ul >li:eq('+opt.next+') .slotholder');
			removeSlots(container,opt,container);
			punchgs.TweenLite.set(nextsh.find('.defaultimg'),{opacity:0});
			actsh.find('.defaultimg').css({'opacity':1});

			nextsh.find('.defaultimg').each(function() {
				var dimg = jQuery(this);

				if (opt.panZoomDisableOnMobile == "on") {
					// NO KEN BURNS ON MOBILE DEVICES

				} else {
					if (dimg.data('kenburn')!=undefined) {
					   dimg.data('kenburn').restart();
					   startKenBurn(container,opt,true)
					}
				}
			});

			var nextli = container.find('>ul >li:eq('+opt.next+')');



			var arr = container.parent().find('.tparrows');
			if (arr.hasClass("preview2"))
				arr.css({width:(parseInt(arr.css('minWidth'),0))});


			animateTheCaptions(nextli, opt,true);
			//restartBannerTimer(opt,container);
			setBulPos(container,opt);

		}




		/*********************************
			-	CHECK IF BROWSER IS IE	-
		********************************/
		var isIE = function( version, comparison ){
		    var $div = jQuery('<div style="display:none;"/>').appendTo(jQuery('body'));
		    $div.html('<!--[if '+(comparison||'')+' IE '+(version||'')+']><a>&nbsp;</a><![endif]-->');
		    var ieTest = $div.find('a').length;
		    $div.remove();
		    return ieTest;
		}



		var callingNewSlide = function(opt,container) {
						// CHECK THE LOOPS !!
						if (opt.next==container.find('>ul >li').length-1) {
								opt.looptogo=opt.looptogo-1;
								if (opt.looptogo<=0)
										opt.stopLoop="on";
							}
						swapSlide(container,opt);

		}






		////////////////////////////////
		//	-	CREATE THE BULLETS -  //
		////////////////////////////////
		var createBullets = function(container,opt) {
			var starthidebullets = "hidebullets";
			if (opt.hideThumbs==0) starthidebullets = "";

			if (opt.navigationType=="bullet"  || opt.navigationType=="both") {
						container.parent().append('<div class="tp-bullets '+starthidebullets+' simplebullets '+opt.navigationStyle+'"></div>');
			}

			var bullets = container.parent().find('.tp-bullets');
			container.find('>ul:first >li').each(function(i) {
							var src=container.find(">ul:first >li:eq("+i+") img:first").attr('src');
							bullets.append('<div class="bullet"></div>');
							var bullet= bullets.find('.bullet:first');
				});
			// ADD THE BULLET CLICK FUNCTION HERE
			bullets.find('.bullet').each(function(i) {
				var bul = jQuery(this);
				if (i==opt.slideamount-1) bul.addClass('last');
				if (i==0) bul.addClass('first');

				bul.click(function() {
					var sameslide = false,
						buli = bul.index();

					if (opt.navigationArrows=="withbullet" || opt.navigationArrows=="nexttobullets")
						buli = bul.index()-1;

					if (buli == opt.act) sameslide=true;

					if (opt.transition==0 && !sameslide) {
						opt.next = buli;
						callingNewSlide(opt,container);
					}
				});

			});
			bullets.append('<div class="tpclear"></div>');
			setBulPos(container,opt);
		}

		//////////////////////
		//	CREATE ARROWS	//
		/////////////////////
		var createArrows = function(container,opt) {
						var bullets = container.find('.tp-bullets'),
							hidden="",
							starthidearrows = "hidearrows",
							arst= opt.navigationStyle;

						if (opt.hideThumbs==0) starthidearrows = "";


						if (opt.navigationArrows=="none") hidden="visibility:hidden;display:none";
						opt.soloArrowStyle = "default"+" "+opt.navigationStyle;

						if (opt.navigationArrows!="none" && opt.navigationArrows!="nexttobullets") arst = opt.soloArrowStyle;

						function aArrow(dir) {
							container.parent().append('<div style="'+hidden+'" class="tp-'+dir+'arrow '+starthidearrows+' tparrows '+arst+'"><div class="tp-arr-allwrapper"><div class="tp-arr-iwrapper"><div class="tp-arr-imgholder"></div><div class="tp-arr-imgholder2"></div><div class="tp-arr-titleholder"></div><div class="tp-arr-subtitleholder"></div></div></div></div>');
						}
						aArrow("left");
						aArrow("right");

						// 	THE LEFT / RIGHT BUTTON CLICK !	 //
						container.parent().find('.tp-rightarrow').click(function() {
							if (opt.transition==0) {
									if (container.data('showus') !=undefined && container.data('showus') != -1)
										opt.next = container.data('showus')-1;
									else
										opt.next = opt.next+1;
									container.data('showus',-1);
									if (opt.next >= opt.slideamount) opt.next=0;
									if (opt.next<0) opt.next=0;

									if (opt.act !=opt.next)
										callingNewSlide(opt,container);
							}
						});

						container.parent().find('.tp-leftarrow').click(function() {
							if (opt.transition==0) {
									opt.next = opt.next-1;
									opt.leftarrowpressed=1;
									if (opt.next < 0) opt.next=opt.slideamount-1;
									callingNewSlide(opt,container);
							}
						});

						setBulPos(container,opt);

		}

		//////////////////////////////////
		//	ENABLE KEYBOARD INTERACTION	//
		//////////////////////////////////
		var createKeyboard = function(container,opt) {
						// 	THE LEFT / RIGHT BUTTON CLICK !	 //
						jQuery(document).keydown(function(e){
							if (opt.transition==0 && e.keyCode == 39) {
									if (container.data('showus') !=undefined && container.data('showus') != -1)
										opt.next = container.data('showus')-1;
									else
										opt.next = opt.next+1;
									container.data('showus',-1);
									if (opt.next >= opt.slideamount) opt.next=0;
									if (opt.next<0) opt.next=0;
									if (opt.act !=opt.next)
										callingNewSlide(opt,container);
							}

							if (opt.transition==0 && e.keyCode == 37) {
									opt.next = opt.next-1;
									opt.leftarrowpressed=1;
									if (opt.next < 0) opt.next=opt.slideamount-1;
									callingNewSlide(opt,container);
							}
						});

						setBulPos(container,opt);

		}

		////////////////////////////
		// SET THE SWIPE FUNCTION //
		////////////////////////////
		var swipeAction = function(container,opt) {
			// TOUCH ENABLED SCROLL
				var aps = "vertical";

				if (opt.touchenabled=="on") {
							if (opt.drag_block_vertical == true)
							    aps = "none";

							container.swipe({
								allowPageScroll:aps,
								fingers:opt.swipe_min_touches,
								treshold:opt.swipe_treshold,
								swipe:function(event,direction,distance,duration,fingerCount,fingerData) {
									switch (direction) {
										case "left":
											 if (opt.transition==0) {
																opt.next = opt.next+1;
																if (opt.next == opt.slideamount) opt.next=0;
																callingNewSlide(opt,container);
														}
										break;
										case "right":
											if (opt.transition==0) {
																opt.next = opt.next-1;
																opt.leftarrowpressed=1;
																if (opt.next < 0) opt.next=opt.slideamount-1;
																callingNewSlide(opt,container);
														}
										break;
										case "up":
											if (aps=="none")
												jQuery("html, body").animate({scrollTop:(container.offset().top + container.height())+"px"});
										break;
										case "down":
											if (aps=="none")
												jQuery("html, body").animate({scrollTop:(container.offset().top - jQuery(window).height())+"px"});
										break;
									}
								}
							})

				}

		}




		////////////////////////////////////////////////////////////////
		// SHOW AND HIDE THE THUMBS IF MOUE GOES OUT OF THE BANNER  ///
		//////////////////////////////////////////////////////////////
		var hideThumbs = function(container,opt) {

			var bullets = container.parent().find('.tp-bullets'),
				ca = container.parent().find('.tparrows');

			if (bullets==null) {
				container.append('<div class=".tp-bullets"></div>');
				var bullets = container.parent().find('.tp-bullets');
			}

			if (ca==null) {
				container.append('<div class=".tparrows"></div>');
				var ca = container.parent().find('.tparrows');
			}


			//var bp = (thumbs.parent().outerHeight(true) - opt.height)/2;

			//	ADD THUMBNAIL IMAGES FOR THE BULLETS //
			container.data('hideThumbs',opt.hideThumbs);

			bullets.addClass("hidebullets");
			ca.addClass("hidearrows");

			if (is_mobile()) {
				try{
					container.hammer().on('touch', function() {
						container.addClass("hovered");
						if (opt.onHoverStop=="on")
							container.trigger('stoptimer');
						clearTimeout(container.data('hideThumbs'));
						bullets.removeClass("hidebullets");
						ca.removeClass("hidearrows");


					});

					container.hammer().on('release', function() {
						container.removeClass("hovered");
						container.trigger('starttimer');
						if (!container.hasClass("hovered") && !bullets.hasClass("hovered"))
							container.data('hideThumbs', setTimeout(function() {
									bullets.addClass("hidebullets");
									ca.addClass("hidearrows");
									container.trigger('starttimer');
							},opt.hideNavDelayOnMobile));
					});
				} catch(e) {}

			} else {
				bullets.hover(function() {
				opt.overnav = true;
				if (opt.onHoverStop=="on")
					container.trigger('stoptimer');
				bullets.addClass("hovered");
				clearTimeout(container.data('hideThumbs'));
				bullets.removeClass("hidebullets");
				ca.removeClass("hidearrows");
					},
				function() {
					opt.overnav = false;
					container.trigger('starttimer');
					bullets.removeClass("hovered");
					if (!container.hasClass("hovered") && !bullets.hasClass("hovered"))
						container.data('hideThumbs', setTimeout(function() {
						bullets.addClass("hidebullets");
						ca.addClass("hidearrows");
						},opt.hideThumbs));
				});


				ca.hover(function() {
					opt.overnav = true;
					if (opt.onHoverStop=="on")
						container.trigger('stoptimer');
					bullets.addClass("hovered");
					clearTimeout(container.data('hideThumbs'));
					bullets.removeClass("hidebullets");
					ca.removeClass("hidearrows");

				},
				function() {
					opt.overnav = false;
					container.trigger('starttimer');
					bullets.removeClass("hovered");
					});



				container.on('mouseenter', function() {
					container.addClass("hovered");
					if (opt.onHoverStop=="on")
						container.trigger('stoptimer');
					clearTimeout(container.data('hideThumbs'));
					bullets.removeClass("hidebullets");
					ca.removeClass("hidearrows");


				});

				container.on('mouseleave', function() {
					container.removeClass("hovered");
					container.trigger('starttimer');
					if (!container.hasClass("hovered") && !bullets.hasClass("hovered"))
						container.data('hideThumbs', setTimeout(function() {
								bullets.addClass("hidebullets");
								ca.addClass("hidearrows");
						},opt.hideThumbs));
				});
			}


		}


		//////////////////////////////
		//	SET POSITION OF BULLETS	//
		//////////////////////////////
		var setBulPos = function(container,opt) {
			var topcont=container.parent();
			var bullets=topcont.find('.tp-bullets');

			if (opt.navigationType=="thumb") {
				bullets.find('.thumb').each(function(i) {
					var thumb = jQuery(this);

					thumb.css({'width':opt.thumbWidth * opt.bw+"px", 'height':opt.thumbHeight*opt.bh+"px"});

				})
				var bup = bullets.find('.tp-mask');

				bup.width(opt.thumbWidth*opt.thumbAmount * opt.bw);
				bup.height(opt.thumbHeight * opt.bh);
				bup.parent().width(opt.thumbWidth*opt.thumbAmount * opt.bw);
				bup.parent().height(opt.thumbHeight * opt.bh);
			}


			var tl = topcont.find('.tp-leftarrow');
			var tr = topcont.find('.tp-rightarrow');

			if (opt.navigationType=="thumb" && opt.navigationArrows=="nexttobullets") opt.navigationArrows="solo";
			// IM CASE WE HAVE NAVIGATION BULLETS TOGETHER WITH ARROWS
			if (opt.navigationArrows=="nexttobullets") {
				tl.prependTo(bullets).css({'float':'left'});
				tr.insertBefore(bullets.find('.tpclear')).css({'float':'left'});
			}
			var loff=0;
			if (opt.forceFullWidth=="on")
						loff = 0-opt.container.parent().offset().left;

			var gridposX = 0,
				gridposY = 0;

			if (opt.navigationInGrid=="on") {
				gridposX = container.width()>opt.startwidth ? (container.width() - opt.startwidth)/2 : 0,
				gridposY = container.height()>opt.startheight ? (container.height() - opt.startheight)/2 : 0;
			}



			if (opt.navigationArrows!="none" && opt.navigationArrows!="nexttobullets") {
				var lv = opt.soloArrowLeftValign,
					lh = opt.soloArrowLeftHalign,
					rv = opt.soloArrowRightValign,
					rh = opt.soloArrowRightHalign,
					lvo = opt.soloArrowLeftVOffset,
					lho = opt.soloArrowLeftHOffset,
					rvo = opt.soloArrowRightVOffset,
					rho = opt.soloArrowRightHOffset;

				tl.css({'position':'absolute'});
				tr.css({'position':'absolute'});

				if (lv=="center")	tl.css({'top':'50%','marginTop':(lvo-Math.round(tl.innerHeight()/2))+"px"})
				else
				if (lv=="bottom")	tl.css({'top':'auto','bottom':(0+lvo)+"px"})
				else
				if (lv=="top")	 	tl.css({'bottom':'auto','top':(0+lvo)+"px"});

				if (lh=="center")	tl.css({'left':'50%','marginLeft':(loff+lho-Math.round(tl.innerWidth()/2))+"px"})
				else
				if (lh=="left")	tl.css({'left':(gridposX+lho+loff)+"px"})
				else
				if (lh=="right")	tl.css({'right':(gridposX+lho-loff)+"px"});

				if (rv=="center")	tr.css({'top':'50%','marginTop':(rvo-Math.round(tr.innerHeight()/2))+"px"})
				else
				if (rv=="bottom")	tr.css({'top':'auto','bottom':(0+rvo)+"px"})
				else
				if (rv=="top")	tr.css({'bottom':'auto','top':(0+rvo)+"px"})

				if (rh=="center")	tr.css({'left':'50%','marginLeft':(loff+rho-Math.round(tr.innerWidth()/2))+"px"})
				else
				if (rh=="left")	tr.css({'left':(gridposX+rho+loff)+"px"})
				else
				if (rh=="right")	tr.css({'right':(gridposX+rho-loff)+"px"})


				if (tl.position()!=null)
					tl.css({'top':Math.round(parseInt(tl.position().top,0))+"px"});

				if (tr.position()!=null)
					tr.css({'top':Math.round(parseInt(tr.position().top,0))+"px"});
			}

			if (opt.navigationArrows=="none") {
				tl.css({'visibility':'hidden'});
				tr.css({'visibility':'hidden'});
			}

			// SET THE POSITIONS OF THE BULLETS // THUMBNAILS
			var nv = opt.navigationVAlign,
				nh = opt.navigationHAlign,
				nvo = opt.navigationVOffset * opt.bh,
				nho = opt.navigationHOffset * opt.bw;

			if (nv=="center")	 bullets.css({'top':'50%','marginTop':(nvo-Math.round(bullets.innerHeight()/2))+"px"});
			if (nv=="bottom")	 bullets.css({'bottom':(0+nvo)+"px"});
			if (nv=="top")	 bullets.css({'top':(0+nvo)+"px"});

			if (nh=="center")	bullets.css({'left':'50%','marginLeft':(loff+nho-Math.round(bullets.innerWidth()/2))+"px"});
			if (nh=="left")	bullets.css({'left':(0+nho+loff)+"px"});
			if (nh=="right")	bullets.css({'right':(0+nho-loff)+"px"});
		}


		/*******************************************************
			-	HANDLING OF PREVIEWS AND CUSTOM PREVIEWS	-
		*******************************************************/

		var handleSpecialPreviews = function(opt) {

			var container= opt.container;
			// FILL WITH INFOS THE NAVIGATION ARROWS
			opt.beforli = opt.next-1;
			opt.comingli = opt.next+1;

			if (opt.beforli<0) opt.beforli = opt.slideamount-1;
			if (opt.comingli>=opt.slideamount) opt.comingli = 0;

			var comingli = container.find('>ul:first-child >li:eq('+opt.comingli+')'),
				beforli = container.find('>ul:first-child >li:eq('+opt.beforli+')'),
				previmgsrc = beforli.find('.defaultimg').attr('src'),
				nextimgsrc = comingli.find('.defaultimg').attr('src');

			// SAVE REFERENCES
			if (opt.arr == undefined) {
				opt.arr = container.parent().find('.tparrows'),
				opt.rar = container.parent().find('.tp-rightarrow'),
				opt.lar = container.parent().find('.tp-leftarrow'),
				opt.raimg = opt.rar.find('.tp-arr-imgholder'),
				opt.laimg = opt.lar.find('.tp-arr-imgholder'),
				opt.raimg_b = opt.rar.find('.tp-arr-imgholder2'),
				opt.laimg_b = opt.lar.find('.tp-arr-imgholder2'),
				opt.ratit = opt.rar.find('.tp-arr-titleholder'),
				opt.latit = opt.lar.find('.tp-arr-titleholder');
			}

			// READ REFERENCES
				var arr = opt.arr,
					rar = opt.rar,
					lar = opt.lar,
					raimg = opt.raimg,
					laimg = opt.laimg,
					raimg_b = opt.raimg_b,
					laimg_b = opt.laimg_b,
					ratit = opt.ratit,
					latit = opt.latit;


			if (comingli.data('title') != undefined) ratit.html(comingli.data('title'));
			if (beforli.data('title') != undefined) latit.html(beforli.data('title'));


			if (rar.hasClass("itishovered")) {
					rar.width(ratit.outerWidth(true)+parseInt(rar.css('minWidth'),0));
				}

			if (lar.hasClass("itishovered")) {
					lar.width(latit.outerWidth(true)+parseInt(lar.css('minWidth'),0));
				}

			if (arr.hasClass("preview2") && !arr.hasClass("hashoveralready")) {

				arr.addClass("hashoveralready");

				if (!is_mobile())
					arr.hover(function() {

						var arr = jQuery(this),
							th = arr.find('.tp-arr-titleholder');
						if (jQuery(window).width()>767)
							arr.width(th.outerWidth(true)+parseInt(arr.css('minWidth'),0));
						arr.addClass("itishovered");
					},function() {
						var arr = jQuery(this),
							th = arr.find('.tp-arr-titleholder');
						arr.css({width:parseInt(arr.css('minWidth'),0)});
						arr.removeClass("itishovered");
					});
				else {
					var arr = jQuery(this),
						th = arr.find('.tp-arr-titleholder');
						th.addClass("alwayshidden");
					punchgs.TweenLite.set(th,{autoAlpha:0});
				}

			}

			if (beforli.data('thumb')!=undefined) previmgsrc = beforli.data('thumb');
			if (comingli.data('thumb')!=undefined) nextimgsrc = comingli.data('thumb')


			// CHANGE THE IMAGE SOURCE (AND ANIMATE IF PREVIEW4 MODE IS ON
			if (!arr.hasClass("preview4")) {

				punchgs.TweenLite.to(raimg,0.5,{autoAlpha:0,onComplete:function() {
					raimg.css({'backgroundImage':'url('+nextimgsrc+')'});
					laimg.css({'backgroundImage':'url('+previmgsrc+')'});
				}});
				punchgs.TweenLite.to(laimg,0.5,{autoAlpha:0,onComplete:function() {
					punchgs.TweenLite.to(raimg,0.5,{autoAlpha:1,delay:0.2});
					punchgs.TweenLite.to(laimg,0.5,{autoAlpha:1,delay:0.2});
				}});
			} else {

				raimg_b.css({'backgroundImage':'url('+nextimgsrc+')'});
				laimg_b.css({'backgroundImage':'url('+previmgsrc+')'});

				punchgs.TweenLite.fromTo(raimg_b,0.8,{force3D:punchgs.force3d,x:0},{x:-raimg.width(),ease:punchgs.Power3.easeOut,delay:1,onComplete:function() {
					raimg.css({'backgroundImage':'url('+nextimgsrc+')'});
					punchgs.TweenLite.set(raimg_b,{x:0});
				}});
				punchgs.TweenLite.fromTo(laimg_b,0.8,{force3D:punchgs.force3d,x:0},{x:raimg.width(),ease:punchgs.Power3.easeOut,delay:1,onComplete:function() {
					laimg.css({'backgroundImage':'url('+previmgsrc+')'});
					punchgs.TweenLite.set(laimg_b,{x:0});
				}});



				punchgs.TweenLite.fromTo(raimg,0.8,{x:0},{force3D:punchgs.force3d,x:-raimg.width(),ease:punchgs.Power3.easeOut,delay:1,onComplete:function() {
					punchgs.TweenLite.set(raimg,{x:0});
				}});
				punchgs.TweenLite.fromTo(laimg,0.8,{x:0},{force3D:punchgs.force3d,x:raimg.width(),ease:punchgs.Power3.easeOut,delay:1,onComplete:function() {
					punchgs.TweenLite.set(laimg,{x:0});
				}});
			}

			// HOVER EFFECTS ARE SPECIAL ON PREVIEW4
			if (rar.hasClass("preview4") && !rar.hasClass("hashoveralready")) {

				rar.addClass("hashoveralready");
				rar.hover(function() {
					var iw = jQuery(this).find('.tp-arr-iwrapper');
					var all = jQuery(this).find('.tp-arr-allwrapper');
					punchgs.TweenLite.fromTo(iw,0.4,{x:iw.width()},{x:0,delay:0.3,ease:punchgs.Power3.easeOut,overwrite:"all"});
					punchgs.TweenLite.to(all,0.2,{autoAlpha:1,overwrite:"all"});

				},function() {
					var iw = jQuery(this).find('.tp-arr-iwrapper');
					var all = jQuery(this).find('.tp-arr-allwrapper');
					punchgs.TweenLite.to(iw,0.4,{x:iw.width(),ease:punchgs.Power3.easeOut,delay:0.2,overwrite:"all"});
					punchgs.TweenLite.to(all,0.2,{delay:0.6,autoAlpha:0,overwrite:"all"});
				});


				lar.hover(function() {
					var iw = jQuery(this).find('.tp-arr-iwrapper');
					var all = jQuery(this).find('.tp-arr-allwrapper');
					punchgs.TweenLite.fromTo(iw,0.4,{x:(0-iw.width())},{x:0,delay:0.3,ease:punchgs.Power3.easeOut,overwrite:"all"});
					punchgs.TweenLite.to(all,0.2,{autoAlpha:1,overwrite:"all"});

				},function() {
					var iw = jQuery(this).find('.tp-arr-iwrapper');
					var all = jQuery(this).find('.tp-arr-allwrapper');
					punchgs.TweenLite.to(iw,0.4,{x:(0-iw.width()),ease:punchgs.Power3.easeOut,delay:0.2,overwrite:"all"});
					punchgs.TweenLite.to(all,0.2,{delay:0.6,autoAlpha:0,overwrite:"all"});
				});

			}
			// END OF NAVIGATION ARROW CONTENT FILLING

		}
		//////////////////////////////////////////////////////////
		//	-	SET THE IMAGE SIZE TO FIT INTO THE CONTIANER -  //
		////////////////////////////////////////////////////////
		var setSize = function(img,opt) {


				opt.container.closest('.forcefullwidth_wrapper_tp_banner').find('.tp-fullwidth-forcer').css({'height':opt.container.height()});
				opt.container.closest('.rev_slider_wrapper').css({'height':opt.container.height()});


				opt.width=parseInt(opt.container.width(),0);
				opt.height=parseInt(opt.container.height(),0);



				opt.bw= (opt.width / opt.startwidth);
				opt.bh = (opt.height / opt.startheight);

				if (opt.bh>opt.bw) opt.bh=opt.bw;
				if (opt.bh<opt.bw) opt.bw = opt.bh;
				if (opt.bw<opt.bh) opt.bh = opt.bw;
				if (opt.bh>1) { opt.bw=1; opt.bh=1; }
				if (opt.bw>1) {opt.bw=1; opt.bh=1; }


				//opt.height= opt.startheight * opt.bh;
				opt.height = Math.round(opt.startheight * (opt.width/opt.startwidth));


				if (opt.height>opt.startheight && opt.autoHeight!="on") opt.height=opt.startheight;


				if (opt.fullScreen=="on") {
						opt.height = opt.bw * opt.startheight;
						var cow = opt.container.parent().width();
						var coh = jQuery(window).height();

						if (opt.fullScreenOffsetContainer!=undefined) {
							try{
								var offcontainers = opt.fullScreenOffsetContainer.split(",");
								jQuery.each(offcontainers,function(index,searchedcont) {
									coh = coh - jQuery(searchedcont).outerHeight(true);
									if (coh<opt.minFullScreenHeight) coh=opt.minFullScreenHeight;
								});
							} catch(e) {}

							 try{

								 if (opt.fullScreenOffset.split("%").length>1 && opt.fullScreenOffset!=undefined && opt.fullScreenOffset.length>0) {

										coh = coh - (jQuery(window).height()* parseInt(opt.fullScreenOffset,0)/100);
								 } else {
								 	if (opt.fullScreenOffset!=undefined && opt.fullScreenOffset.length>0)
								 		coh = coh - parseInt(opt.fullScreenOffset,0);
								 }


								 if (coh<opt.minFullScreenHeight) coh=opt.minFullScreenHeight;

							} catch(e) {}
						}

						opt.container.parent().height(coh);

						opt.container.closest('.rev_slider_wrapper').height(coh);
						opt.container.css({'height':'100%'});

						opt.height=coh;
						if (opt.minHeight!=undefined && opt.height<opt.minHeight)
							opt.height = opt.minHeight;
				} else {
						if (opt.minHeight!=undefined && opt.height<opt.minHeight)
							opt.height = opt.minHeight;

						opt.container.height(opt.height);
				}


				opt.slotw=Math.ceil(opt.width/opt.slots);

				if (opt.fullScreen=="on")
					opt.sloth=Math.ceil(jQuery(window).height()/opt.slots);
				else
					opt.sloth=Math.ceil(opt.height/opt.slots);

				if (opt.autoHeight=="on")
				 	opt.sloth=Math.ceil(img.height()/opt.slots);




		}




		/////////////////////////////////////////
		//	-	PREPARE THE SLIDES / SLOTS -  //
		///////////////////////////////////////
		var prepareSlides = function(container,opt) {

			container.find('.tp-caption').each(function() { jQuery(this).addClass(jQuery(this).data('transition')); jQuery(this).addClass('start') });

			// PREPARE THE UL CONTAINER TO HAVEING MAX HEIGHT AND HEIGHT FOR ANY SITUATION
			container.find('>ul:first').css({overflow:'hidden',width:'100%',height:'100%',maxHeight:container.parent().css('maxHeight')}).addClass("tp-revslider-mainul");
			if (opt.autoHeight=="on") {
			   container.find('>ul:first').css({overflow:'hidden',width:'100%',height:'100%',maxHeight:"none"});
			   container.css({'maxHeight':'none'});
			   container.parent().css({'maxHeight':'none'});
			 }

			container.find('>ul:first >li').each(function(j) {
				var li=jQuery(this);
				li.addClass("tp-revslider-slidesli");

				// MAKE LI OVERFLOW HIDDEN FOR FURTHER ISSUES
				li.css({'width':'100%','height':'100%','overflow':'hidden'});

				// IF LINK ON SLIDE EXISTS, NEED TO CREATE A PROPER LAYER FOR IT.
				if (li.data('link')!=undefined) {
					var link = li.data('link');
					var target="_self";
					var zindex=60;
					if (li.data('slideindex')=="back") zindex=0;
					var linktoslide=checksl = li.data('linktoslide');
					if (linktoslide != undefined) {
						if (linktoslide!="next" && linktoslide!="prev")
							container.find('>ul:first-child >li').each(function() {
									var t = jQuery(this);
									if (t.data('origindex')+1==checksl) linktoslide = t.index()+1;
							});
					}
					if (li.data('target')!=undefined) target=li.data('target');
					if (link!="slide") linktoslide="no";
					var apptxt = '<div class="tp-caption sft slidelink" style="width:100%;height:100%;z-index:'+zindex+';" data-x="center" data-y="center" data-linktoslide="'+linktoslide+'" data-start="0"><a style="width:100%;height:100%;display:block"';
					if (link!="slide") apptxt = apptxt + ' target="'+target+'" href="'+link+'"';
					apptxt = apptxt + '><span style="width:100%;height:100%;display:block"></span></a></div>';

					li.append(apptxt);
				}
			});

			// RESOLVE OVERFLOW HIDDEN OF MAIN CONTAINER
			container.parent().css({'overflow':'visible'});


			container.find('>ul:first >li >img').each(function(j) {

				var img=jQuery(this);

				img.addClass('defaultimg');
				if (img.data('lazyload')!=undefined && img.data('lazydone') != 1) {

				} else {
					setSize(img,opt);
				}

				if (isIE(8)) {
					img.data('kenburns',"off");
				}

				// TURN OF KEN BURNS IF WE ARE ON MOBILE AND IT IS WISHED SO
				if (opt.panZoomDisableOnMobile == "on"  && is_mobile()) {
					img.data('kenburns',"off");
					img.data('bgfit',"cover");
				}

				img.wrap('<div class="slotholder" style="width:100%;height:100%;"'+
						  'data-duration="'+img.data('duration')+'"'+
						  'data-zoomstart="'+img.data("zoomstart")+'"'+
						  'data-zoomend="'+img.data("zoomend")+'"'+
						  'data-rotationstart="'+img.data("rotationstart")+'"'+
						  'data-rotationend="'+img.data("rotationend")+'"'+
						  'data-ease="'+img.data("ease")+'"'+
						  'data-duration="'+img.data("duration")+'"'+
						  'data-bgpositionend="'+img.data("bgpositionend")+'"'+
						  'data-bgposition="'+img.data("bgposition")+'"'+
						  'data-duration="'+img.data("duration")+'"'+
						  'data-kenburns="'+img.data("kenburns")+'"'+
						  'data-easeme="'+img.data("ease")+'"'+
						  'data-bgfit="'+img.data("bgfit")+'"'+
						  'data-bgfitend="'+img.data("bgfitend")+'"'+
						  'data-owidth="'+img.data("owidth")+'"'+
						  'data-oheight="'+img.data("oheight")+'"'+
						  '></div>');

				if (opt.dottedOverlay!="none" && opt.dottedOverlay!=undefined)
						img.closest('.slotholder').append('<div class="tp-dottedoverlay '+opt.dottedOverlay+'"></div>');

				var src=img.attr('src'),
					ll = img.data('lazyload'),
					bgfit = img.data('bgfit'),
					bgrepeat = img.data('bgrepeat'),
					bgposition = img.data('bgposition');


				if (bgfit==undefined) bgfit="cover";
				if (bgrepeat==undefined) bgrepeat="no-repeat";
				if (bgposition==undefined) bgposition="center center"


				var pari = img.closest('.slotholder');
				img.replaceWith('<div class="tp-bgimg defaultimg" data-lazyload="'+img.data('lazyload')+'" data-bgfit="'+bgfit+'"data-bgposition="'+bgposition+'" data-bgrepeat="'+bgrepeat+'" data-lazydone="'+img.data('lazydone')+'" src="'+src+'" data-src="'+src+'" style="background-color:'+img.css("backgroundColor")+';background-repeat:'+bgrepeat+';background-image:url('+src+');background-size:'+bgfit+';background-position:'+bgposition+';width:100%;height:100%;"></div>');

				if (isIE(8)) {
					pari.find('.tp-bgimg').css({backgroundImage:"none",'background-image':'none'});
					pari.find('.tp-bgimg').append('<img class="ieeightfallbackimage defaultimg" src="'+src+'" style="width:100%">');
				}

				img.css({'opacity':0});
				img.data('li-id',j);

			});
		}


		///////////////////////
		// PREPARE THE SLIDE //
		//////////////////////
		var prepareOneSlide = function(slotholder,opt,visible,vorh) {

				var sh=slotholder,
					img = sh.find('.defaultimg'),
					scalestart = sh.data('zoomstart'),
					rotatestart = sh.data('rotationstart');

				if (img.data('currotate')!=undefined)
					rotatestart = img.data('currotate');
				if (img.data('curscale')!=undefined && vorh=="box")
					scalestart = img.data('curscale')*100;
				else
				if (img.data('curscale')!=undefined)
					scalestart = img.data('curscale');

				setSize(img,opt)

				var src = img.data('src'),
					bgcolor=img.css('backgroundColor'),
					w = opt.width,
					h = opt.height,
					fulloff = img.data("fxof"),
					fullyoff=0;

				if (opt.autoHeight=="on") h = opt.container.height();
				if (fulloff==undefined) fulloff=0;



				var off=0,
					bgfit = img.data('bgfit'),
					bgrepeat = img.data('bgrepeat'),
					bgposition = img.data('bgposition');

				if (bgfit==undefined) bgfit="cover";
				if (bgrepeat==undefined) bgrepeat="no-repeat";
				if (bgposition==undefined) bgposition="center center";

				if (isIE(8)) {
					sh.data('kenburns',"off");
					var imgsrc=src;
			    	src="";
				}

				switch (vorh) {
					// BOX ANIMATION PREPARING
					case "box":
						// SET THE MINIMAL SIZE OF A BOX
						var basicsize = 0,
							x = 0,
							y = 0;

						if (opt.sloth>opt.slotw)
							basicsize=opt.sloth
						else
							basicsize=opt.slotw;

						if (!visible) {
							var off=0-basicsize;
						}

						opt.slotw = basicsize;
						opt.sloth = basicsize;
						var x=0;
						var y=0;

						if (sh.data('kenburns')=="on") {
						   bgfit=scalestart;
						   if (bgfit.toString().length<4)
							   bgfit = calculateKenBurnScales(bgfit,sh,opt);
						 }

						for (var j=0;j<opt.slots;j++) {

							y=0;
							for (var i=0;i<opt.slots;i++) 	{


								sh.append('<div class="slot" '+
										  'style="position:absolute;'+
													'top:'+(fullyoff+y)+'px;'+
													'left:'+(fulloff+x)+'px;'+
													'width:'+basicsize+'px;'+
													'height:'+basicsize+'px;'+
													'overflow:hidden;">'+

										  '<div class="slotslide" data-x="'+x+'" data-y="'+y+'" '+
										  			'style="position:absolute;'+
													'top:'+(0)+'px;'+
													'left:'+(0)+'px;'+
													'width:'+basicsize+'px;'+
													'height:'+basicsize+'px;'+
													'overflow:hidden;">'+

										  '<div style="position:absolute;'+
													'top:'+(0-y)+'px;'+
													'left:'+(0-x)+'px;'+
													'width:'+w+'px;'+
													'height:'+h+'px;'+
													'background-color:'+bgcolor+';'+
													'background-image:url('+src+');'+
													'background-repeat:'+bgrepeat+';'+
													'background-size:'+bgfit+';background-position:'+bgposition+';">'+
										  '</div></div></div>');
								y=y+basicsize;

								if (isIE(8)) {

									sh.find('.slot ').last().find('.slotslide').append('<img src="'+imgsrc+'">');
									ieimgposition(sh,opt);
								}

								if (scalestart!=undefined && rotatestart!=undefined)
										punchgs.TweenLite.set(sh.find('.slot').last(),{rotationZ:rotatestart});
							}
							x=x+basicsize;
						}
					break;

					// SLOT ANIMATION PREPARING
					case "vertical":
					case "horizontal":
						if (sh.data('kenburns')=="on") {
						   bgfit=scalestart;
						   if (bgfit.toString().length<4)
							   bgfit = calculateKenBurnScales(bgfit,sh,opt);
						 }
						 if (vorh == "horizontal") {
							if (!visible) var off=0-opt.slotw;
							for (var i=0;i<opt.slots;i++) {
									sh.append('<div class="slot" style="position:absolute;'+
																	'top:'+(0+fullyoff)+'px;'+
																	'left:'+(fulloff+(i*opt.slotw))+'px;'+
																	'overflow:hidden;width:'+(opt.slotw+0.6)+'px;'+
																	'height:'+h+'px">'+
									'<div class="slotslide" style="position:absolute;'+
																	'top:0px;left:'+off+'px;'+
																	'width:'+(opt.slotw+0.6)+'px;'+
																	'height:'+h+'px;overflow:hidden;">'+
									'<div style="background-color:'+bgcolor+';'+
																	'position:absolute;top:0px;'+
																	'left:'+(0-(i*opt.slotw))+'px;'+
																	'width:'+w+'px;height:'+h+'px;'+
																	'background-image:url('+src+');'+
																	'background-repeat:'+bgrepeat+';'+
																	'background-size:'+bgfit+';background-position:'+bgposition+';">'+
									'</div></div></div>');
									if (scalestart!=undefined && rotatestart!=undefined)
										punchgs.TweenLite.set(sh.find('.slot').last(),{rotationZ:rotatestart});
									if (isIE(8)) {
									   sh.find('.slot ').last().find('.slotslide').append('<img class="ieeightfallbackimage" src="'+imgsrc+'" style="width:100%;height:auto">');
									   ieimgposition(sh,opt);
								}
							}
						} else {
							if (!visible) var off=0-opt.sloth;
							for (var i=0;i<opt.slots+2;i++) {
								sh.append('<div class="slot" style="position:absolute;'+
														 'top:'+(fullyoff+(i*opt.sloth))+'px;'+
														 'left:'+(fulloff)+'px;'+
														 'overflow:hidden;'+
														 'width:'+w+'px;'+
														 'height:'+(opt.sloth)+'px">'+

											 '<div class="slotslide" style="position:absolute;'+
																 'top:'+(off)+'px;'+
																 'left:0px;width:'+w+'px;'+
																 'height:'+opt.sloth+'px;'+
																 'overflow:hidden;">'+
											'<div style="background-color:'+bgcolor+';'+
																	'position:absolute;'+
																	'top:'+(0-(i*opt.sloth))+'px;'+
																	'left:0px;'+
																	'width:'+w+'px;height:'+h+'px;'+
																	'background-image:url('+src+');'+
																	'background-repeat:'+bgrepeat+';'+
																	'background-size:'+bgfit+';background-position:'+bgposition+';">'+

											'</div></div></div>');
									if (scalestart!=undefined && rotatestart!=undefined)
										punchgs.TweenLite.set(sh.find('.slot').last(),{rotationZ:rotatestart});
									if (isIE(8)) {
								    	sh.find('.slot ').last().find('.slotslide').append('<img class="ieeightfallbackimage" src="'+imgsrc+'" style="width:100%;height:auto;">');
								    	ieimgposition(sh,opt);
									}
							}
						}
					break;
				}
		}

		/***********************************************
			-	MOVE IE8 IMAGE IN RIGHT POSITION	-
		***********************************************/

		var ieimgposition = function(nextsh,opt) {

			if (isIE(8)) {

					var ie8img = nextsh.find('.ieeightfallbackimage');

					var ie8w = ie8img.width(),
						ie8h = ie8img.height();



					if (opt.startwidth/opt.startheight <nextsh.data('owidth')/nextsh.data('oheight'))
						ie8img.css({width:"auto",height:"100%"})
					else
						ie8img.css({width:"100%",height:"auto"})


					setTimeout(function() {

						var ie8w = ie8img.width(),
						    ie8h = ie8img.height(),
						    bgp = nextsh.data('bgposition');


						if (bgp=="center center")
							ie8img.css({position:"absolute",top:opt.height/2 - ie8h/2+"px", left:opt.width/2-ie8w/2+"px"});

						if (bgp=="center top" || bgp=="top center")
							ie8img.css({position:"absolute",top:"0px", left:opt.width/2-ie8w/2+"px"});

						if (bgp=="center bottom" || bgp=="bottom center")
							ie8img.css({position:"absolute",bottom:"0px", left:opt.width/2-ie8w/2+"px"});


						if (bgp=="right top" || bgp=="top right")
							ie8img.css({position:"absolute",top:"0px", right:"0px"});

						if (bgp=="right bottom" || bgp=="bottom right")
							ie8img.css({position:"absolute",bottom:"0px", right:"0px"});

						if (bgp=="right center" || bgp=="center right")
							ie8img.css({position:"absolute",top:opt.height/2 - ie8h/2+"px", right:"0px"});

						if (bgp=="left bottom" || bgp=="bottom left")
							ie8img.css({position:"absolute",bottom:"0px", left:"0px"});

						if (bgp=="left center" || bgp=="center left")
							ie8img.css({position:"absolute",top:opt.height/2 - ie8h/2+"px", left:"0px"});
					},20);
				}
		}

		///////////////////////
		//	REMOVE SLOTS	//
		/////////////////////
		var removeSlots = function(container,opt,where) {
				where.find('.slot').each(function() {
					jQuery(this).remove();
				});
				opt.transition = 0;
		}


		/*******************************************
			-	PREPARE LOADING OF IMAGES	-
		********************************************/
		var loadAllPrepared = function(container,alreadyinload) {

			container.find('img, .defaultimg').each(function(i) {
				var img = jQuery(this),
					ill = img.data('lazyload');

				if (ill!=img.attr('src') && alreadyinload<3 && ill!=undefined && ill!='undefined') {

					if (ill !=undefined && ill !='undefined') {
						img.attr('src',ill);

						var limg = new Image();

						limg.onload = function(i) {
							img.data('lazydone',1);
							if (img.hasClass("defaultimg")) setDefImg(img,limg);
						}
						limg.error = function() {
							img.data('lazydone',1);
						}

						limg.src=img.attr('src');
						if (limg.complete) {
								if (img.hasClass("defaultimg")) setDefImg(img,limg);
								img.data('lazydone',1);
						}

					}
				} else {

					if ((ill === undefined || ill === 'undefined') && img.data('lazydone')!=1) {
						var limg = new Image();
						limg.onload = function() {
							if (img.hasClass("defaultimg")) setDefImg(img,limg);
							img.data('lazydone',1);
						}
						limg.error = function() {
							img.data('lazydone',1);
						}


						if (img.attr('src')!=undefined && img.attr('src')!='undefined') 	{
							limg.src = img.attr('src');
						} else
							limg.src = img.data('src');

						if (limg.complete) {
								if (img.hasClass("defaultimg")) {
									setDefImg(img,limg);
								}
								img.data('lazydone',1);
						}
					}
				}
			})
		}

		var setDefImg = function(img,limg) {
			var nextli = img.closest('li'),
				ww = limg.width,
				hh = limg.height;

			nextli.data('owidth',ww);
			nextli.data('oheight',hh);
			nextli.find('.slotholder').data('owidth',ww);
			nextli.find('.slotholder').data('oheight',hh);
			nextli.data('loadeddone',1);
		}

		var waitForLoads = function(element,call,opt) {

			loadAllPrepared(element,0);
			var inter = setInterval(function() {
				opt.bannertimeronpause = true;
				opt.container.trigger('stoptimer');
				opt.cd=0;
				 var found = 0;
				 element.find('img, .defaultimg').each(function(i) {
				 	if (jQuery(this).data('lazydone')!=1) {
				 		found++;

				 	}
				 });

				 if (found>0)
					 loadAllPrepared(element,found);
				 else {
					 clearInterval(inter);
					 if (call!=undefined)
					 	call();
				 }

			},100)
		}


		//////////////////////////////
		//	-	SWAP THE SLIDES -  //
		////////////////////////////
		var swapSlide = function(container,opt) {

				try{
					var actli =container.find('>ul:first-child >li:eq('+opt.act+')');
				} catch(e) {
					var actli=container.find('>ul:first-child >li:eq(1)');
				}
				opt.lastslide=opt.act;
				var nextli = container.find('>ul:first-child >li:eq('+opt.next+')');

				var defimg= nextli.find('.defaultimg');


				opt.bannertimeronpause = true;
				container.trigger('stoptimer');
				opt.cd=0;

				if (defimg.data('lazyload') !=undefined && defimg.data('lazyload') !="undefined" && defimg.data('lazydone') !=1 ) {

					if (!isIE(8))
						defimg.css({backgroundImage:'url("'+nextli.find('.defaultimg').data('lazyload')+'")'});
					else {
						defimg.attr('src',nextli.find('.defaultimg').data('lazyload'));
					}

					defimg.data('src',nextli.find('.defaultimg').data('lazyload'));
					defimg.data('lazydone',1);
					defimg.data('orgw',0);
					nextli.data('loadeddone',1);

					container.find('.tp-loader').css({display:"block"});
					waitForLoads(container.find('.tp-static-layers'),function() {
						waitForLoads(nextli,function() {
								var nextsh = nextli.find('.slotholder');
								if (nextsh.data('kenburns')=="on") {
									var waitfordimension = setInterval(function() {
										var ow = nextsh.data('owidth');
										if (ow>=0) {
											clearInterval(waitfordimension);
											swapSlideCall(opt,defimg,container)
										}
									},10)
								} else
								 swapSlideCall(opt,defimg,container)
						},opt);
					},opt);

				} else {

					if (nextli.data('loadeddone')===undefined) {
						nextli.data('loadeddone',1);
						waitForLoads(nextli,function() {
							  swapSlideCall(opt,defimg,container)
							},opt);
					} else

					 swapSlideCall(opt,defimg,container)
				}

		}

		var swapSlideCall = function(opt,defimg,container) {
			opt.bannertimeronpause = false;
		    opt.cd=0;
		    container.trigger('nulltimer');
		    container.find('.tp-loader').css({display:"none"});
		    setSize(defimg,opt);
			setBulPos(container,opt);
			setSize(defimg,opt);
		   	swapSlideProgress(container,opt);

		}

		/******************************
			-	SWAP SLIDE PROGRESS	-
		********************************/
		/*!SWAP SLIDE*/
		var swapSlideProgress = function(container,opt) {


			container.trigger('revolution.slide.onbeforeswap');

			opt.transition = 1;
			opt.videoplaying = false;
			//konsole.log("VideoPlay set to False due swapSlideProgress");

			try{
				var actli = container.find('>ul:first-child >li:eq('+opt.act+')');
			} catch(e) {
				var actli=container.find('>ul:first-child >li:eq(1)');
			}

			opt.lastslide=opt.act;

			var nextli = container.find('>ul:first-child >li:eq('+opt.next+')');

			setTimeout(function() {
				handleSpecialPreviews(opt);
			},200);

			var actsh = actli.find('.slotholder'),
				nextsh = nextli.find('.slotholder');

			if (nextsh.data('kenburns')=="on" || actsh.data('kenburns')=="on") {
				stopKenBurn(container,opt);
				container.find('.kenburnimg').remove();
			}


			// IF DELAY HAS BEEN SET VIA THE SLIDE, WE TAKE THE NEW VALUE, OTHER WAY THE OLD ONE...
			if (nextli.data('delay')!=undefined) {
						opt.cd=0;
						opt.delay=nextli.data('delay');
			} else {
				opt.delay=opt.origcd;
			}


			if (opt.firststart==1)
				punchgs.TweenLite.set(actli,{autoAlpha:0});

			punchgs.TweenLite.set(actli,{zIndex:18});
			punchgs.TweenLite.set(nextli,{autoAlpha:0,zIndex:20});

			///////////////////////////
			//	REMOVE THE CAPTIONS //
			///////////////////////////
			var removetime = 0;
			if (actli.index() != nextli.index() && opt.firststart!=1) {
				removetime = removeTheCaptions(actli,opt);

			}

			if (actli.data('saveperformance')!="on") removetime = 0;

			setTimeout(function() {
				//opt.cd=0;
			    //container.trigger('nulltimer');
			    container.trigger('restarttimer');
				slideAnimation(container,opt,nextli,actli,actsh,nextsh);
			},removetime)

		}


		/******************************************
			-	START THE LAYER ANIMATION 	-
		*******************************************/

		var slideAnimation = function(container,opt,nextli,actli,actsh,nextsh) {

			// IF THERE IS AN OTHER FIRST SLIDE START HAS BEED SELECTED
			if (nextli.data('differentissplayed') =='prepared') {
				nextli.data('differentissplayed','done');
				nextli.data('transition',nextli.data('savedtransition'));
				nextli.data('slotamount',nextli.data('savedslotamount'));
				nextli.data('masterspeed',nextli.data('savedmasterspeed'));
			}


			if (nextli.data('fstransition') != undefined && nextli.data('differentissplayed') !="done") {
				nextli.data('savedtransition',nextli.data('transition'));
				nextli.data('savedslotamount',nextli.data('slotamount'));
				nextli.data('savedmasterspeed',nextli.data('masterspeed'));

				nextli.data('transition',nextli.data('fstransition'));
				nextli.data('slotamount',nextli.data('fsslotamount'));
				nextli.data('masterspeed',nextli.data('fsmasterspeed'));

				nextli.data('differentissplayed','prepared');
			}

			container.find('.active-revslide').removeClass('.active-revslide');
			nextli.addClass("active-revslide");

			///////////////////////////////////////
			// TRANSITION CHOOSE - RANDOM EFFECTS//
			///////////////////////////////////////


			if (nextli.data('transition')==undefined) nextli.data('transition',"random");

			var nexttrans = 0,
				transtext = nextli.data('transition').split(","),
				curtransid = nextli.data('nexttransid') == undefined ? -1 : nextli.data('nexttransid');

			if (nextli.data('randomtransition')=="on")
				curtransid = Math.round(Math.random()*transtext.length);
			else
				curtransid=curtransid+1;

			if (curtransid==transtext.length) curtransid=0;
			nextli.data('nexttransid',curtransid);



			var comingtransition = transtext[curtransid];

			if (opt.ie) {
				if (comingtransition=="boxfade") comingtransition = "boxslide";
				if (comingtransition=="slotfade-vertical") comingtransition = "slotzoom-vertical";
				if (comingtransition=="slotfade-horizontal") comingtransition = "slotzoom-horizontal";
			}

			if (isIE(8)) {
				comingtransition = 11;
			}


			var specials = 0;

			if (opt.parallax=="scroll" && opt.parallaxFirstGo==undefined) {
				opt.parallaxFirstGo = true;
				scrollParallax(container,opt);
				setTimeout(function() {
					scrollParallax(container,opt);
				},210);
				setTimeout(function() {
					scrollParallax(container,opt);
				},420);

			}




		/*	if (opt.ffnn == undefined) opt.ffnn=0;
			comingtransition=opt.ffnn;

			if ( direction==1)
				opt.ffnn=opt.ffnn-1;
			else
				opt.ffnn=opt.ffnn+1;

			if (opt.ffnn>46) opt.ffnn=0;
			if (opt.ffnn<0) opt.ffnn = 46;

			jQuery('.logo').html('Next Anim:'+comingtransition);


			if (comingtransition=="boxslide" || comingtransition == "boxfade" || comingtransition == "papercut" ||
				comingtransition==0 || comingtransition == 1 || comingtransition == 16)
				comingtransition = 9;*/


			/* Transition Name ,
			   Transition Code,
			   Transition Sub Code,
			   Max Slots,
			   MasterSpeed Delays,
			   Preparing Slots (box,slideh, slidev),
			   Call on nextsh (null = no, true/false for visibility first preparing),
			   Call on actsh (null = no, true/false for visibility first preparing),
			*/



			if (comingtransition=="slidehorizontal") {
						comingtransition = "slideleft"
					if (opt.leftarrowpressed==1)
						comingtransition = "slideright"
				}

			if (comingtransition=="slidevertical") {
						comingtransition = "slideup"
					if (opt.leftarrowpressed==1)
						comingtransition = "slidedown"
				}

			if (comingtransition=="parallaxhorizontal") {
						comingtransition = "parallaxtoleft"
					if (opt.leftarrowpressed==1)
						comingtransition = "parallaxtoright"
				}


			if (comingtransition=="parallaxvertical") {
						comingtransition = "parallaxtotop"
					if (opt.leftarrowpressed==1)
						comingtransition = "parallaxtobottom"
				}




			var transitionsArray = [ ['boxslide' , 0, 1, 10, 0,'box',false,null,0],
									 ['boxfade', 1, 0, 10, 0,'box',false,null,1],
									 ['slotslide-horizontal', 2, 0, 0, 200,'horizontal',true,false,2],
									 ['slotslide-vertical', 3, 0,0,200,'vertical',true,false,3],
									 ['curtain-1', 4, 3,0,0,'horizontal',true,true,4],
									 ['curtain-2', 5, 3,0,0,'horizontal',true,true,5],
									 ['curtain-3', 6, 3,25,0,'horizontal',true,true,6],
									 ['slotzoom-horizontal', 7, 0,0,400,'horizontal',true,true,7],
									 ['slotzoom-vertical', 8, 0,0,0,'vertical',true,true,8],
									 ['slotfade-horizontal', 9, 0,0,500,'horizontal',true,null,9],
									 ['slotfade-vertical', 10, 0,0 ,500,'vertical',true,null,10],
									 ['fade', 11, 0, 1 ,300,'horizontal',true,null,11],
									 ['slideleft', 12, 0,1,0,'horizontal',true,true,12],
									 ['slideup', 13, 0,1,0,'horizontal',true,true,13],
									 ['slidedown', 14, 0,1,0,'horizontal',true,true,14],
									 ['slideright', 15, 0,1,0,'horizontal',true,true,15],
									 ['papercut', 16, 0,0,600,'',null,null,16],
									 ['3dcurtain-horizontal', 17, 0,20,100,'vertical',false,true,17],
									 ['3dcurtain-vertical', 18, 0,10,100,'horizontal',false,true,18],
									 ['cubic', 19, 0,20,600,'horizontal',false,true,19],
									 ['cube',19,0,20,600,'horizontal',false,true,20],
									 ['flyin', 20, 0,4,600,'vertical',false,true,21],
									 ['turnoff', 21, 0,1,1600,'horizontal',false,true,22],
									 ['incube', 22, 0,20,200,'horizontal',false,true,23],
									 ['cubic-horizontal', 23, 0,20,500,'vertical',false,true,24],
									 ['cube-horizontal', 23, 0,20,500,'vertical',false,true,25],
									 ['incube-horizontal', 24, 0,20,500,'vertical',false,true,26],
									 ['turnoff-vertical', 25, 0,1,200,'horizontal',false,true,27],
									 ['fadefromright', 12, 1,1,0,'horizontal',true,true,28],
									 ['fadefromleft', 15, 1,1,0,'horizontal',true,true,29],
									 ['fadefromtop', 14, 1,1,0,'horizontal',true,true,30],
									 ['fadefrombottom', 13, 1,1,0,'horizontal',true,true,31],
									 ['fadetoleftfadefromright', 12, 2,1,0,'horizontal',true,true,32],
									 ['fadetorightfadetoleft', 15, 2,1,0,'horizontal',true,true,33],
									 ['fadetobottomfadefromtop', 14, 2,1,0,'horizontal',true,true,34],
									 ['fadetotopfadefrombottom', 13, 2,1,0,'horizontal',true,true,35],
									 ['parallaxtoright', 12, 3,1,0,'horizontal',true,true,36],
									 ['parallaxtoleft', 15, 3,1,0,'horizontal',true,true,37],
									 ['parallaxtotop', 14, 3,1,0,'horizontal',true,true,38],
									 ['parallaxtobottom', 13, 3,1,0,'horizontal',true,true,39],
									 ['scaledownfromright', 12, 4,1,0,'horizontal',true,true,40],
									 ['scaledownfromleft', 15, 4,1,0,'horizontal',true,true,41],
									 ['scaledownfromtop', 14, 4,1,0,'horizontal',true,true,42],
									 ['scaledownfrombottom', 13, 4,1,0,'horizontal',true,true,43],
									 ['zoomout', 13, 5,1,0,'horizontal',true,true,44],
									 ['zoomin', 13, 6,1,0,'horizontal',true,true,45],
									 ['notransition',26,0,1,0,'horizontal',true,null,46]
								   ];


			var flatTransitions = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45];
			var premiumTransitions = [16,17,18,19,20,21,22,23,24,25,26,27]

			var nexttrans =0;
			var specials = 1;
			var STAindex = 0;
			var indexcounter =0;
			var STA = new Array;

			//START THE KEN BURN PAN ZOOM ANIMATION
			if (nextsh.data('kenburns')=="on") {
					if (comingtransition == "boxslide" || comingtransition==0 ||
						comingtransition == "boxfade" || comingtransition==1 ||
						comingtransition == "papercut" || comingtransition==16
						)
						comingtransition = 11;

						startKenBurn(container,opt,true,true);
			}



			// RANDOM TRANSITIONS
			if (comingtransition == "random") {
				comingtransition = Math.round(Math.random()*transitionsArray.length-1);
				if (comingtransition>transitionsArray.length-1) comingtransition=transitionsArray.length-1;
			}

			// RANDOM FLAT TRANSITIONS
			if (comingtransition == "random-static") {
				comingtransition = Math.round(Math.random()*flatTransitions.length-1);
				if (comingtransition>flatTransitions.length-1) comingtransition=flatTransitions.length-1;
				comingtransition = flatTransitions[comingtransition];
			}

			// RANDOM PREMIUM TRANSITIONS
			if (comingtransition == "random-premium") {
				comingtransition = Math.round(Math.random()*premiumTransitions.length-1);
				if (comingtransition>premiumTransitions.length-1) comingtransition=premiumTransitions.length-1;
				comingtransition = premiumTransitions[comingtransition];
			}

			//joomla only change: avoid problematic transitions that don't compatible with mootools
			var problematicTransitions = [12,13,14,15,16,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45];
			if(opt.isJoomla == true && window.MooTools != undefined && problematicTransitions.indexOf(comingtransition) != -1){

				var newTransIndex = Math.round(Math.random() * (premiumTransitions.length-2) ) + 1;

				//some limits fix
				if (newTransIndex > premiumTransitions.length-1)
					newTransIndex = premiumTransitions.length-1;

				if(newTransIndex == 0)
					newTransIndex = 1;

				comingtransition = premiumTransitions[newTransIndex];
			}



			function findTransition() {
				// FIND THE RIGHT TRANSITION PARAMETERS HERE
				jQuery.each(transitionsArray,function(inde,trans) {
					if (trans[0] == comingtransition || trans[8] == comingtransition) {
						nexttrans = trans[1];
						specials = trans[2];
						STAindex = indexcounter;
					}
					indexcounter = indexcounter+1;
				})
			}

			findTransition();

			// CHECK IF WE HAVE IE8 AND THAN FALL BACK ON FLAT TRANSITIONS
			if (isIE(8) && nexttrans>15 && nexttrans<28) {
				comingtransition = Math.round(Math.random()*flatTransitions.length-1);
				if (comingtransition>flatTransitions.length-1) comingtransition=flatTransitions.length-1;
				comingtransition = flatTransitions[comingtransition];
				indexcounter =0;
				findTransition();
			}




			// WHICH DIRECTION DID WE HAD ?
			var direction=-1;
			if (opt.leftarrowpressed==1 || opt.act>opt.next) direction=1;



			opt.leftarrowpressed=0;

			if (nexttrans>26) nexttrans = 26;
			if (nexttrans<0) nexttrans = 0;


			// DEFINE THE MASTERSPEED FOR THE SLIDE //
			var masterspeed=300;
			if (nextli.data('masterspeed')!=undefined && nextli.data('masterspeed')>99 && nextli.data('masterspeed')<opt.delay)
				masterspeed = nextli.data('masterspeed');
			if (nextli.data('masterspeed')!=undefined && nextli.data('masterspeed')>opt.delay)
				masterspeed = opt.delay;

			// PREPARED DEFAULT SETTINGS PER TRANSITION
			STA = transitionsArray[STAindex];

			/////////////////////////////////////////////
			// SET THE BULLETS SELECTED OR UNSELECTED  //
			/////////////////////////////////////////////
			container.parent().find(".bullet").each(function() {
				var bul = jQuery(this),
					buli = bul.index();
				bul.removeClass("selected");

				if (opt.navigationArrows=="withbullet" || opt.navigationArrows=="nexttobullets")
					buli = bul.index()-1;

				if (buli == opt.next) bul.addClass('selected');

			});

			///////////////////////////////
			//	MAIN TIMELINE DEFINITION //
			///////////////////////////////

			var mtl = new punchgs.TimelineLite({onComplete:function() {
							letItFree(container,opt,nextsh,actsh,nextli,actli,mtl);
						}});
			//SET DEFAULT IMG UNVISIBLE AT START
			mtl.add(punchgs.TweenLite.set(nextsh.find('.defaultimg'),{opacity:0}));
			mtl.pause();




			/////////////////////////////////////////////
			//	SET THE ACTUAL AMOUNT OF SLIDES !!     //
			//  SET A RANDOM AMOUNT OF SLOTS          //
			///////////////////////////////////////////
			if (nextli.data('slotamount')==undefined || nextli.data('slotamount')<1) {
				opt.slots=Math.round(Math.random()*12+4);
				if (comingtransition=="boxslide")
					opt.slots=Math.round(Math.random()*6+3);
				else
				if (comingtransition=="flyin")
					opt.slots=Math.round(Math.random()*4+1);
			 } else {
				opt.slots=nextli.data('slotamount');

			}

			/////////////////////////////////////////////
			//	SET THE ACTUAL AMOUNT OF SLIDES !!     //
			//  SET A RANDOM AMOUNT OF SLOTS          //
			///////////////////////////////////////////
			if (nextli.data('rotate')==undefined)
				opt.rotate = 0
			 else
				if (nextli.data('rotate')==999)
					opt.rotate=Math.round(Math.random()*360);
				 else
				    opt.rotate=nextli.data('rotate');
			if (!jQuery.support.transition  || opt.ie || opt.ie9) opt.rotate=0;




			//////////////////////////////
			//	FIRST START 			//
			//////////////////////////////
			if (opt.firststart==1) opt.firststart=0;


			// ADJUST MASTERSPEED
			masterspeed = masterspeed + STA[4];

			if ((nexttrans==4 || nexttrans==5 || nexttrans==6) && opt.slots<3 ) opt.slots=3;

			// ADJUST SLOTS
			if (STA[3] != 0) opt.slots = Math.min(opt.slots,STA[3]);
			if (nexttrans==9) opt.slots = opt.width/20;
			if (nexttrans==10) opt.slots = opt.height/20;

			// prepareOneSlide

			if (STA[7] !=null) prepareOneSlide(actsh,opt,STA[7],STA[5]);
			if (STA[6] !=null) prepareOneSlide(nextsh,opt,STA[6],STA[5]);


			/////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION I.  //
			////////////////////////////////////
			if (nexttrans==0) {								// BOXSLIDE


						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						var maxz = Math.ceil(opt.height/opt.sloth);
						var curz = 0;
						nextsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);
							curz=curz+1;
							if (curz==maxz) curz=0;

							mtl.add(punchgs.TweenLite.from(ss,(masterspeed)/600,
												{opacity:0,top:(0-opt.sloth),left:(0-opt.slotw),rotation:opt.rotate,force3D:"auto",ease:punchgs.Power2.easeOut}),((j*15) + ((curz)*30))/1500);
						});
			}
			/////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION I.  //
			////////////////////////////////////
			if (nexttrans==1) {

						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						var maxtime,
							maxj = 0;

						nextsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this),
								rand=Math.random()*masterspeed+300,
								rand2=Math.random()*500+200;
							if (rand+rand2>maxtime) {
								maxtime = rand2+rand2;
								maxj = j;
							}
							mtl.add(punchgs.TweenLite.from(ss,rand/1000,
										{autoAlpha:0, force3D:"auto",rotation:opt.rotate,ease:punchgs.Power2.easeInOut}),rand2/1000);
						});
			}


			/////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION I.  //
			////////////////////////////////////
			if (nexttrans==2) {

						var subtl = new punchgs.TimelineLite();
						// ALL OLD SLOTS SHOULD BE SLIDED TO THE RIGHT
						actsh.find('.slotslide').each(function() {
							var ss=jQuery(this);
							subtl.add(punchgs.TweenLite.to(ss,masterspeed/1000,{left:opt.slotw, force3D:"auto",rotation:(0-opt.rotate)}),0);
							mtl.add(subtl,0);
						});

						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						nextsh.find('.slotslide').each(function() {
							var ss=jQuery(this);
							subtl.add(punchgs.TweenLite.from(ss,masterspeed/1000,{left:0-opt.slotw, force3D:"auto",rotation:opt.rotate}),0);
							mtl.add(subtl,0);
						});
			}



			/////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION I.  //
			////////////////////////////////////
			if (nexttrans==3) {
						var subtl = new punchgs.TimelineLite();

						// ALL OLD SLOTS SHOULD BE SLIDED TO THE RIGHT
						actsh.find('.slotslide').each(function() {
							var ss=jQuery(this);
							subtl.add(punchgs.TweenLite.to(ss,masterspeed/1000,{top:opt.sloth,rotation:opt.rotate,force3D:"auto",transformPerspective:600}),0);
							mtl.add(subtl,0);

						});

						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						nextsh.find('.slotslide').each(function() {
							var ss=jQuery(this);
							subtl.add(punchgs.TweenLite.from(ss,masterspeed/1000,{top:0-opt.sloth,rotation:opt.rotate,ease:punchgs.Power2.easeOut,force3D:"auto",transformPerspective:600}),0);
							mtl.add(subtl,0);
						});
			}



			/////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION I.  //
			////////////////////////////////////
			if (nexttrans==4 || nexttrans==5) {

						setTimeout(function() {
							actsh.find('.defaultimg').css({opacity:0});
						},100);


						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						var cspeed = (masterspeed)/1000,
							ticker = cspeed,
							subtl = new punchgs.TimelineLite();

						actsh.find('.slotslide').each(function(i) {
							var ss=jQuery(this);
							var del = (i*cspeed)/opt.slots;
							if (nexttrans==5) del = ((opt.slots-i-1)*cspeed)/(opt.slots)/1.5;
							subtl.add(punchgs.TweenLite.to(ss,cspeed*3,{transformPerspective:600,force3D:"auto",top:0+opt.height,opacity:0.5,rotation:opt.rotate,ease:punchgs.Power2.easeInOut,delay:del}),0);
							mtl.add(subtl,0);
						});

						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						nextsh.find('.slotslide').each(function(i) {
							var ss=jQuery(this);
							var del = (i*cspeed)/opt.slots;
							if (nexttrans==5) del = ((opt.slots-i-1)*cspeed)/(opt.slots)/1.5;
							subtl.add(punchgs.TweenLite.from(ss,cspeed*3,
											{top:(0-opt.height),opacity:0.5,rotation:opt.rotate,force3D:"auto",ease:punchgs.Power2.easeInOut,delay:del}),0);
							mtl.add(subtl,0);

						});


			}

			/////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION I.  //
			////////////////////////////////////
			if (nexttrans==6) {


						if (opt.slots<2) opt.slots=2;
						if (opt.slots % 2) opt.slots = opt.slots+1;

						var subtl = new punchgs.TimelineLite();

						//SET DEFAULT IMG UNVISIBLE
						setTimeout(function() {
							actsh.find('.defaultimg').css({opacity:0});
						},100);

						actsh.find('.slotslide').each(function(i) {
							var ss=jQuery(this);
							if (i+1<opt.slots/2)
								var tempo = (i+2)*90;
							else
								var tempo = (2+opt.slots-i)*90;

							subtl.add(punchgs.TweenLite.to(ss,(masterspeed+tempo)/1000,{top:0+opt.height,opacity:1,force3D:"auto",rotation:opt.rotate,ease:punchgs.Power2.easeInOut}),0);
							mtl.add(subtl,0);
						});

						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						nextsh.find('.slotslide').each(function(i) {
							var ss=jQuery(this);

							if (i+1<opt.slots/2)
								var tempo = (i+2)*90;
							else
								var tempo = (2+opt.slots-i)*90;

							subtl.add(punchgs.TweenLite.from(ss,(masterspeed+tempo)/1000,
													{top:(0-opt.height),opacity:1,force3D:"auto",rotation:opt.rotate,ease:punchgs.Power2.easeInOut}),0);
							mtl.add(subtl,0);
						});
			}


			////////////////////////////////////
			// THE SLOTSZOOM - TRANSITION II. //
			////////////////////////////////////
			if (nexttrans==7) {

						masterspeed = masterspeed *2;
						if (masterspeed>opt.delay) masterspeed=opt.delay;
						var subtl = new punchgs.TimelineLite();

						//SET DEFAULT IMG UNVISIBLE
						setTimeout(function() {
							actsh.find('.defaultimg').css({opacity:0});
						},100);

						// ALL OLD SLOTS SHOULD BE SLIDED TO THE RIGHT
						actsh.find('.slotslide').each(function() {
							var ss=jQuery(this).find('div');
							subtl.add(punchgs.TweenLite.to(ss,masterspeed/1000,{
									left:(0-opt.slotw/2)+'px',
									top:(0-opt.height/2)+'px',
									width:(opt.slotw*2)+"px",
									height:(opt.height*2)+"px",
									opacity:0,
									rotation:opt.rotate,
									force3D:"auto",
									ease:punchgs.Power2.easeOut}),0);
							mtl.add(subtl,0);

						});

						//////////////////////////////////////////////////////////////
						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT //
						///////////////////////////////////////////////////////////////
						nextsh.find('.slotslide').each(function(i) {
							var ss=jQuery(this).find('div');

							subtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
										{left:0,top:0,opacity:0,transformPerspective:600},
										{left:(0-i*opt.slotw)+'px',
										 ease:punchgs.Power2.easeOut,
										 force3D:"auto",
									     top:(0)+'px',
									     width:opt.width,
									     height:opt.height,
										 opacity:1,rotation:0,
										 delay:0.1}),0);
							mtl.add(subtl,0);
						});
			}




			////////////////////////////////////
			// THE SLOTSZOOM - TRANSITION II. //
			////////////////////////////////////
			if (nexttrans==8) {

						masterspeed = masterspeed * 3;
						if (masterspeed>opt.delay) masterspeed=opt.delay;
						var subtl = new punchgs.TimelineLite();



						// ALL OLD SLOTS SHOULD BE SLIDED TO THE RIGHT
						actsh.find('.slotslide').each(function() {
							var ss=jQuery(this).find('div');
							subtl.add(punchgs.TweenLite.to(ss,masterspeed/1000,
										  {left:(0-opt.width/2)+'px',
										   top:(0-opt.sloth/2)+'px',
										   width:(opt.width*2)+"px",
										   height:(opt.sloth*2)+"px",
										   force3D:"auto",
										   opacity:0,rotation:opt.rotate}),0);
							mtl.add(subtl,0);

						});


						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT //
						///////////////////////////////////////////////////////////////
						nextsh.find('.slotslide').each(function(i) {
							var ss=jQuery(this).find('div');

							subtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
										  {left:0, top:0,opacity:0,force3D:"auto"},
										  {'left':(0)+'px',
										   'top':(0-i*opt.sloth)+'px',
										   'width':(nextsh.find('.defaultimg').data('neww'))+"px",
										   'height':(nextsh.find('.defaultimg').data('newh'))+"px",
										   opacity:1,rotation:0,
										   }),0);
							mtl.add(subtl,0);
						});
			}


			////////////////////////////////////////
			// THE SLOTSFADE - TRANSITION III.   //
			//////////////////////////////////////
			if (nexttrans==9 || nexttrans==10) {
						var ssamount=0;
						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						nextsh.find('.slotslide').each(function(i) {
							var ss=jQuery(this);
							ssamount++;
							mtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,{autoAlpha:0,force3D:"auto",transformPerspective:600},
																				 {autoAlpha:1,ease:punchgs.Power2.easeInOut,delay:(i*5)/1000}),0);

						});
			}

			///////////////////////////
			// SIMPLE FADE ANIMATION //
			///////////////////////////
			if (nexttrans==11 || nexttrans==26) {


						var ssamount=0;
						if (nexttrans==26) masterspeed=0;

						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						nextsh.find('.slotslide').each(function(i) {
							var ss=jQuery(this);
							mtl.add(punchgs.TweenLite.from(ss,masterspeed/1000,{autoAlpha:0,force3D:"auto",ease:punchgs.Power2.easeInOut}),0);
						});
			}

			if (nexttrans==12 || nexttrans==13 || nexttrans==14 || nexttrans==15) {
						masterspeed = masterspeed;
						if (masterspeed>opt.delay) masterspeed=opt.delay;
						//masterspeed = 1000;

						setTimeout(function() {
							punchgs.TweenLite.set(actsh.find('.defaultimg'),{autoAlpha:0});

						},100);

						var oow = opt.width,
							ooh = opt.height,
							ssn=nextsh.find('.slotslide'),
							twx = 0,
							twy = 0,
							op = 1,
							scal = 1,
							fromscale = 1,
							easeitout = punchgs.Power2.easeInOut,
							easeitin = punchgs.Power2.easeInOut,
							speedy = masterspeed/1000,
							speedy2 = speedy;


						if (opt.fullWidth=="on" || opt.fullScreen=="on") {
							oow=ssn.width();
							ooh=ssn.height();
						}

						if (nexttrans==12)
							twx = oow;
						else
						if (nexttrans==15)
							twx = 0-oow;
						else
						if (nexttrans==13)
							twy = ooh;
						else
						if (nexttrans==14)
							twy = 0-ooh;


						// DEPENDING ON EXTENDED SPECIALS, DIFFERENT SCALE AND OPACITY FUNCTIONS NEED TO BE ADDED
						if (specials == 1) op = 0;
						if (specials == 2) op = 0;
						if (specials == 3) {
								easeitout = punchgs.Power2.easeInOut;
								easeitin = punchgs.Power1.easeInOut;
								speedy = masterspeed / 1200;
						}

						if (specials==4 || specials==5)
							scal=0.6;
						if (specials==6 )
							scal=1.4;


						if (specials==5 || specials==6) {
						    fromscale=1.4;
						    op=0;
						    oow=0;
						    ooh=0;twx=0;twy=0;
						 }
						if (specials==6) fromscale=0.6;
						var dd = 0;

						mtl.add(punchgs.TweenLite.from(ssn,speedy,
										{left:twx, top:twy, scale:fromscale, opacity:op,rotation:opt.rotate,ease:easeitin,force3D:"auto"}),0);

						var ssa=actsh.find('.slotslide');

						if (specials==4 || specials==5) {
							oow = 0; ooh=0;
						}

						if (specials!=1)
							switch (nexttrans) {
								case 12:
									mtl.add(punchgs.TweenLite.to(ssa,speedy2,{'left':(0-oow)+'px',force3D:"auto",scale:scal,opacity:op,rotation:opt.rotate,ease:easeitout}),0);
								break;
								case 15:
									mtl.add(punchgs.TweenLite.to(ssa,speedy2,{'left':(oow)+'px',force3D:"auto",scale:scal,opacity:op,rotation:opt.rotate,ease:easeitout}),0);
								break;
								case 13:
									mtl.add(punchgs.TweenLite.to(ssa,speedy2,{'top':(0-ooh)+'px',force3D:"auto",scale:scal,opacity:op,rotation:opt.rotate,ease:easeitout}),0);
								break;
								case 14:
									mtl.add(punchgs.TweenLite.to(ssa,speedy2,{'top':(ooh)+'px',force3D:"auto",scale:scal,opacity:op,rotation:opt.rotate,ease:easeitout}),0);
								break;
							}

			}

			//////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION XVI.  //
			//////////////////////////////////////
			if (nexttrans==16) {						// PAPERCUT


					var subtl = new punchgs.TimelineLite();
					mtl.add(punchgs.TweenLite.set(actli,{'position':'absolute','z-index':20}),0);
					mtl.add(punchgs.TweenLite.set(nextli,{'position':'absolute','z-index':15}),0);


					// PREPARE THE CUTS
					actli.wrapInner('<div class="tp-half-one" style="position:relative; width:100%;height:100%"></div>');

					actli.find('.tp-half-one').clone(true).appendTo(actli).addClass("tp-half-two");
					actli.find('.tp-half-two').removeClass('tp-half-one');

					var oow = opt.width,
						ooh = opt.height;
					if (opt.autoHeight=="on")
						ooh = container.height();


					actli.find('.tp-half-one .defaultimg').wrap('<div class="tp-papercut" style="width:'+oow+'px;height:'+ooh+'px;"></div>')
					actli.find('.tp-half-two .defaultimg').wrap('<div class="tp-papercut" style="width:'+oow+'px;height:'+ooh+'px;"></div>')
					actli.find('.tp-half-two .defaultimg').css({position:'absolute',top:'-50%'});
					actli.find('.tp-half-two .tp-caption').wrapAll('<div style="position:absolute;top:-50%;left:0px;"></div>');

					mtl.add(punchgs.TweenLite.set(actli.find('.tp-half-two'),
					                 {width:oow,height:ooh,overflow:'hidden',zIndex:15,position:'absolute',top:ooh/2,left:'0px',transformPerspective:600,transformOrigin:"center bottom"}),0);

					mtl.add(punchgs.TweenLite.set(actli.find('.tp-half-one'),
					                 {width:oow,height:ooh/2,overflow:'visible',zIndex:10,position:'absolute',top:'0px',left:'0px',transformPerspective:600,transformOrigin:"center top"}),0);

					// ANIMATE THE CUTS
					var img=actli.find('.defaultimg'),
						ro1=Math.round(Math.random()*20-10),
						ro2=Math.round(Math.random()*20-10),
						ro3=Math.round(Math.random()*20-10),
						xof = Math.random()*0.4-0.2,
						yof = Math.random()*0.4-0.2,
						sc1=Math.random()*1+1,
						sc2=Math.random()*1+1,
						sc3=Math.random()*0.3+0.3;

					mtl.add(punchgs.TweenLite.set(actli.find('.tp-half-one'),{overflow:'hidden'}),0);
					mtl.add(punchgs.TweenLite.fromTo(actli.find('.tp-half-one'),masterspeed/800,
					                 {width:oow,height:ooh/2,position:'absolute',top:'0px',left:'0px',force3D:"auto",transformOrigin:"center top"},
					                 {scale:sc1,rotation:ro1,y:(0-ooh-ooh/4),autoAlpha:0,ease:punchgs.Power2.easeInOut}),0);
					mtl.add(punchgs.TweenLite.fromTo(actli.find('.tp-half-two'),masterspeed/800,
					                 {width:oow,height:ooh,overflow:'hidden',position:'absolute',top:ooh/2,left:'0px',force3D:"auto",transformOrigin:"center bottom"},
					                 {scale:sc2,rotation:ro2,y:ooh+ooh/4,ease:punchgs.Power2.easeInOut,autoAlpha:0,onComplete:function() {
						                // CLEAN UP
										punchgs.TweenLite.set(actli,{'position':'absolute','z-index':15});
										punchgs.TweenLite.set(nextli,{'position':'absolute','z-index':20});
										if (actli.find('.tp-half-one').length>0)  {
											actli.find('.tp-half-one .defaultimg').unwrap();
											actli.find('.tp-half-one .slotholder').unwrap();
										}
										actli.find('.tp-half-two').remove();
					                 }}),0);

					subtl.add(punchgs.TweenLite.set(nextsh.find('.defaultimg'),{autoAlpha:1}),0);

					if (actli.html()!=null)
						mtl.add(punchgs.TweenLite.fromTo(nextli,(masterspeed-200)/1000,
														{scale:sc3,x:(opt.width/4)*xof, y:(ooh/4)*yof,rotation:ro3,force3D:"auto",transformOrigin:"center center",ease:punchgs.Power2.easeOut},
														{autoAlpha:1,scale:1,x:0,y:0,rotation:0}),0);

					mtl.add(subtl,0);


			}

			////////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION XVII.  //
			///////////////////////////////////////
			if (nexttrans==17) {								// 3D CURTAIN HORIZONTAL


						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT

						nextsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);

							mtl.add(punchgs.TweenLite.fromTo(ss,(masterspeed)/800,
											{opacity:0,rotationY:0,scale:0.9,rotationX:-110,force3D:"auto",transformPerspective:600,transformOrigin:"center center"},
											{opacity:1,top:0,left:0,scale:1,rotation:0,rotationX:0,force3D:"auto",rotationY:0,ease:punchgs.Power3.easeOut,delay:j*0.06}),0);

						});
			}



			////////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION XVIII.  //
			///////////////////////////////////////
			if (nexttrans==18) {								// 3D CURTAIN VERTICAL

						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						nextsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);

							mtl.add(punchgs.TweenLite.fromTo(ss,(masterspeed)/500,
											{autoAlpha:0,rotationY:310,scale:0.9,rotationX:10,force3D:"auto",transformPerspective:600,transformOrigin:"center center"},
											{autoAlpha:1,top:0,left:0,scale:1,rotation:0,rotationX:0,force3D:"auto",rotationY:0,ease:punchgs.Power3.easeOut,delay:j*0.06}),0);
						});



			}


			////////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION XIX.  //
			///////////////////////////////////////
			if (nexttrans==19 || nexttrans==22) {								// IN CUBE

						var subtl = new punchgs.TimelineLite();
						//SET DEFAULT IMG UNVISIBLE

						mtl.add(punchgs.TweenLite.set(actli,{zIndex:20}),0);
						mtl.add(punchgs.TweenLite.set(nextli,{zIndex:20}),0);
						setTimeout(function() {
							actsh.find('.defaultimg').css({opacity:0});
						},100);
						var chix=nextli.css('z-index'),
							chix2=actli.css('z-index'),
							rot = 90,
							op = 1,
							torig ="center center ";

						if (direction==1) rot = -90;

						if (nexttrans==19) {
							torig = torig+"-"+opt.height/2;
							op=0;

						} else {
							torig = torig+opt.height/2;
						}

						// ALL NEW SLOTS SHOULD BE SLIDED FROM THE LEFT TO THE RIGHT
						punchgs.TweenLite.set(container,{transformStyle:"flat",backfaceVisibility:"hidden",transformPerspective:600});

						nextsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);

							subtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
											{transformStyle:"flat",backfaceVisibility:"hidden",left:0,rotationY:opt.rotate,z:10,top:0,scale:1,force3D:"auto",transformPerspective:600,transformOrigin:torig,rotationX:rot},
											{left:0,rotationY:0,top:0,z:0, scale:1,force3D:"auto",rotationX:0, delay:(j*50)/1000,ease:punchgs.Power2.easeInOut}),0);
							subtl.add(punchgs.TweenLite.to(ss,0.1,{autoAlpha:1,delay:(j*50)/1000}),0);
							mtl.add(subtl);
						});

						actsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);
							var rot = -90;
							if (direction==1) rot = 90;

							subtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
											{transformStyle:"flat",backfaceVisibility:"hidden",autoAlpha:1,rotationY:0,top:0,z:0,scale:1,force3D:"auto",transformPerspective:600,transformOrigin:torig, rotationX:0},
											{autoAlpha:1,rotationY:opt.rotate,top:0,z:10, scale:1,rotationX:rot, delay:(j*50)/1000,force3D:"auto",ease:punchgs.Power2.easeInOut}),0);

							mtl.add(subtl);
						});
			}




			////////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION XX.  //
			///////////////////////////////////////
			if (nexttrans==20 ) {								// FLYIN


						setTimeout(function() {
							actsh.find('.defaultimg').css({opacity:0});
						},100);
						var chix=nextli.css('z-index'),
							chix2=actli.css('z-index');

						if (direction==1) {
						   var ofx = -opt.width
						   var rot  =70;
						   var torig = "left center -"+opt.height/2;
						} else {
							var ofx = opt.width;
							var rot = -70;
							var torig = "right center -"+opt.height/2;
						}


						nextsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);

							mtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1500,
											{left:ofx,rotationX:40,z:-600, opacity:op,top:0,force3D:"auto",transformPerspective:600,transformOrigin:torig,rotationY:rot},
											{left:0, delay:(j*50)/1000,ease:punchgs.Power2.easeInOut}),0);

							mtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
											{rotationX:40,z:-600, opacity:op,top:0,scale:1,force3D:"auto",transformPerspective:600,transformOrigin:torig,rotationY:rot},
											{rotationX:0,opacity:1,top:0,z:0, scale:1,rotationY:0, delay:(j*50)/1000,ease:punchgs.Power2.easeInOut}),0);

							mtl.add(punchgs.TweenLite.to(ss,0.1,{opacity:1,force3D:"auto",delay:(j*50)/1000+masterspeed/2000}),0);

						});
						actsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);

							if (direction!=1) {
							   var ofx = -opt.width
							   var rot  =70;
							   var torig = "left center -"+opt.height/2;
							} else {
								var ofx = opt.width;
								var rot = -70;
								var torig = "right center -"+opt.height/2;
							}
							mtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
											{opacity:1,rotationX:0,top:0,z:0,scale:1,left:0, force3D:"auto",transformPerspective:600,transformOrigin:torig, rotationY:0},
											{opacity:1,rotationX:40,top:0, z:-600, left:ofx, force3D:"auto",scale:0.8,rotationY:rot, delay:(j*50)/1000,ease:punchgs.Power2.easeInOut}),0);
							mtl.add(punchgs.TweenLite.to(ss,0.1,{force3D:"auto",opacity:0,delay:(j*50)/1000+(masterspeed/1000 - (masterspeed/10000))}),0);
						});
			}

			////////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION XX.  //
			///////////////////////////////////////
			if (nexttrans==21 || nexttrans==25) {								// TURNOFF


						//SET DEFAULT IMG UNVISIBLE

						setTimeout(function() {
							actsh.find('.defaultimg').css({opacity:0});
						},100);
						var chix=nextli.css('z-index'),
							chix2=actli.css('z-index'),
							rot = 90,
							ofx = -opt.width,
							rot2 = -rot;

						if (direction==1) {
						   if (nexttrans==25) {
						   	 var torig = "center top 0";
						   	 rot = opt.rotate;
						   } else {
						     var torig = "left center 0";
						     rot2 = opt.rotate;
						   }

						} else {
							ofx = opt.width;
							rot = -90;
							if (nexttrans==25) {
						   	 var torig = "center bottom 0"
						   	 rot2 = -rot;
						   	 rot = opt.rotate;
						   } else {
						     var torig = "right center 0";
						     rot2 = opt.rotate;
						   }
						}

						nextsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);


							mtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
											{left:0,transformStyle:"flat",rotationX:rot2,z:0, autoAlpha:0,top:0,scale:1,force3D:"auto",transformPerspective:600,transformOrigin:torig,rotationY:rot},
											{left:0,rotationX:0,top:0,z:0, autoAlpha:1,scale:1,rotationY:0,force3D:"auto", ease:punchgs.Power3.easeInOut}),0);
						});


						if (direction!=1) {
						   	ofx = -opt.width
						   	rot  = 90;

						   if (nexttrans==25) {
						   	 torig = "center top 0"
						   	 rot2 = -rot;
						   	 rot = opt.rotate;
						   } else {
						     torig = "left center 0";
						     rot2 = opt.rotate;
						   }

						} else {
							ofx = opt.width;
							rot = -90;
							if (nexttrans==25) {
						   	 torig = "center bottom 0"
						   	 rot2 = -rot;
						   	 rot = opt.rotate;
						   } else {
						     torig = "right center 0";
						     rot2 = opt.rotate;
						   }
						}

						actsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);
							mtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
											{left:0,transformStyle:"flat",rotationX:0,z:0, autoAlpha:1,top:0,scale:1,force3D:"auto",transformPerspective:600,transformOrigin:torig,rotationY:0},
											{left:0,rotationX:rot2,top:0,z:0,autoAlpha:1,force3D:"auto", scale:1,rotationY:rot,ease:punchgs.Power1.easeInOut}),0);
						});
			}



			////////////////////////////////////////
			// THE SLOTSLIDE - TRANSITION XX.  //
			///////////////////////////////////////
			if (nexttrans==23 || nexttrans == 24) {								// cube-horizontal - inboxhorizontal


						//SET DEFAULT IMG UNVISIBLE
						setTimeout(function() {
							actsh.find('.defaultimg').css({opacity:0});
						},100);
						var chix=nextli.css('z-index'),
							chix2=actli.css('z-index'),
							rot = -90,
							op = 1,
							opx=0;

						if (direction==1) rot = 90;
						if (nexttrans==23) {
							var torig = "center center -"+opt.width/2;
							op=0;
						} else
							var torig = "center center "+opt.width/2;

						punchgs.TweenLite.set(container,{transformStyle:"preserve-3d",backfaceVisibility:"hidden",perspective:2500});
										nextsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);
							mtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
											{left:opx,rotationX:opt.rotate,force3D:"auto",opacity:op,top:0,scale:1,transformPerspective:600,transformOrigin:torig,rotationY:rot},
											{left:0,rotationX:0,autoAlpha:1,top:0,z:0, scale:1,rotationY:0, delay:(j*50)/500,ease:punchgs.Power2.easeInOut}),0);
						});

						rot = 90;
						if (direction==1) rot = -90;

						actsh.find('.slotslide').each(function(j) {
							var ss=jQuery(this);
							mtl.add(punchgs.TweenLite.fromTo(ss,masterspeed/1000,
											{left:0,autoAlpha:1,rotationX:0,top:0,z:0,scale:1,force3D:"auto",transformPerspective:600,transformOrigin:torig, rotationY:0},
											{left:opx,autoAlpha:1,rotationX:opt.rotate,top:0, scale:1,rotationY:rot, delay:(j*50)/500,ease:punchgs.Power2.easeInOut}),0);



						});
								}


			// SHOW FIRST LI && ANIMATE THE CAPTIONS
			mtl.pause();
			animateTheCaptions(nextli, opt,null,mtl);
			punchgs.TweenLite.to(nextli,0.001,{autoAlpha:1});

			var data={};
			data.slideIndex=opt.next+1;
			data.slide = nextli;
			container.trigger('revolution.slide.onchange',data);
			setTimeout(function() { container.trigger('revolution.slide.onafterswap'); },masterspeed);
			container.trigger('revolution.slide.onvideostop');

		}






		/**************************************
			-	GIVE FREE THE TRANSITIOSN	-
		**************************************/
		var letItFree = function(container,opt,nextsh,actsh,nextli,actli,mtl) {
					punchgs.TweenLite.to(nextsh.find('.defaultimg'),0.001,{autoAlpha:1,onComplete:function() {
						removeSlots(container,opt,nextli);
					}});
					if (nextli.index()!=actli.index()) {
						punchgs.TweenLite.to(actli,0.2,{autoAlpha:0,onComplete:function() {
							removeSlots(container,opt,actli);
						}});
					}
					opt.act=opt.next;
					if (opt.navigationType=="thumb") moveSelectedThumb(container);
					if (nextsh.data('kenburns')=="on") {
						startKenBurn(container,opt);
					}
					container.find('.current-sr-slide-visible').removeClass("current-sr-slide-visible");
					nextli.addClass("current-sr-slide-visible");
					if (opt.parallax=="scroll" || opt.parallax=="scroll+mouse" || opt.parallax=="mouse+scroll") {
								scrollParallax(container,opt);
					}

					mtl.clear();

			}


		//////////////////////////////////////////
		// CHANG THE YOUTUBE PLAYER STATE HERE //
		////////////////////////////////////////
		var  onPlayerStateChange = function(event) {

			 var embedCode = event.target.getVideoEmbedCode();
			 var ytcont = jQuery('#'+embedCode.split('id="')[1].split('"')[0])
			 var container = ytcont.closest('.tp-simpleresponsive');
			 var player = ytcont.parent().data('player');

			if (event.data == YT.PlayerState.PLAYING) {

				var bt = container.find('.tp-bannertimer');
				var opt = bt.data('opt');


				if (ytcont.closest('.tp-caption').data('volume')=="mute")
					  player.mute();

				opt.videoplaying=true;
				container.trigger('stoptimer');
				container.trigger('revolution.slide.onvideoplay');

			} else {

				var bt = container.find('.tp-bannertimer');
				var opt = bt.data('opt');

				if ((event.data!=-1 && event.data!=3)) {

					opt.videoplaying=false;
					container.trigger('starttimer');
					container.trigger('revolution.slide.onvideostop');

				}

				if (event.data==0 && opt.nextslideatend==true)
					opt.container.revnext();
				else {

					opt.videoplaying=false;
					container.trigger('starttimer');
					container.trigger('revolution.slide.onvideostop');
				}

			}


		  }



		 ////////////////////////
		// VIMEO ADD EVENT /////
		////////////////////////
		var addEvent = function(element, eventName, callback) {

					if (element.addEventListener)
						element.addEventListener(eventName, callback, false);
					else
						element.attachEvent(eventName, callback, false);
		}





		/////////////////////////////////////
		// EVENT HANDLING FOR VIMEO VIDEOS //
		/////////////////////////////////////

		var vimeoready_auto = function(player_id,autoplay) {

			var froogaloop = $f(player_id),
				vimcont = jQuery('#'+player_id),
				container = vimcont.closest('.tp-simpleresponsive'),
				nextcaption = vimcont.closest('.tp-caption');

			setTimeout(function() {
				froogaloop.addEvent('ready', function(data) {
						if(autoplay) froogaloop.api('play');


							froogaloop.addEvent('play', function(data) {
								var bt = container.find('.tp-bannertimer');
								var opt = bt.data('opt');

								opt.videoplaying=true;
								container.trigger('stoptimer');
								if (nextcaption.data('volume')=="mute")
								  froogaloop.api('setVolume',"0");
							});

							froogaloop.addEvent('finish', function(data) {
									var bt = container.find('.tp-bannertimer');
									var opt = bt.data('opt');
									opt.videoplaying=false;
									container.trigger('starttimer');

									container.trigger('revolution.slide.onvideoplay'); //opt.videostartednow=1;
									if (opt.nextslideatend==true)
										opt.container.revnext();

							});

							froogaloop.addEvent('pause', function(data) {
									var bt = container.find('.tp-bannertimer');
									var opt = bt.data('opt');
									opt.videoplaying=false;
									container.trigger('starttimer');
									container.trigger('revolution.slide.onvideostop'); //opt.videostoppednow=1;
							});

						// PLAY VIDEO IF THUMBNAIL HAS BEEN CLICKED
						 nextcaption.find('.tp-thumb-image').click(function() {
							 punchgs.TweenLite.to(jQuery(this),0.3,{autoAlpha:0,force3D:"auto",ease:punchgs.Power3.easeInOut})
							 froogaloop.api("play");
						 })
					});
				},150);
			}



			/////////////////////////////////////
			// RESIZE HTML5VIDEO FOR FULLSCREEN//
			/////////////////////////////////////
			var updateHTML5Size = function(pc,container) {
					var windowW = container.width();
					var windowH = container.height();
					var mediaAspect = pc.data('mediaAspect');
					if (mediaAspect == undefined) mediaAspect = 1;


					var windowAspect = windowW/windowH;

					pc.css({position:"absolute"});
					var video = pc.find('video');


					if (windowAspect < mediaAspect) {
						// taller
						punchgs.TweenLite.to(pc,0.0001,{width:windowH*mediaAspect,force3D:"auto",top:0,
												left:0-(windowH*mediaAspect-windowW)/2,
												height:windowH});

					} else {
						// wider
						punchgs.TweenLite.to(pc,0.0001,{width:windowW,force3D:"auto",top:0-(windowW/mediaAspect-windowH)/2,
												left:0,
												height:windowW/mediaAspect});
					}
				}



				/////////////////////////////////////
				//	-	CREATE ANIMATION OBJECT	-  //
				/////////////////////////////////////
				var newAnimObject = function() {
										var a = new Object();
										a.x=0;
										a.y=0;
										a.rotationX = 0;
										a.rotationY = 0;
										a.rotationZ = 0;
										a.scale = 1;
										a.scaleX = 1;
										a.scaleY = 1;
										a.skewX = 0;
										a.skewY = 0;
										a.opacity=0;
										a.transformOrigin = "center, center";
										a.transformPerspective = 400;
										a.rotation = 0;
										return a;
									}

				///////////////////////////////////////////////////
				// ANALYSE AND READ OUT DATAS FROM HTML CAPTIONS //
				///////////////////////////////////////////////////
				var getAnimDatas = function(frm,data) {

									var customarray = data.split(';');
									jQuery.each(customarray,function(index,param) {

										param = param.split(":")

										var w = param[0],
											v = param[1];
										if (w=="rotationX") frm.rotationX = parseInt(v,0);
										if (w=="rotationY") frm.rotationY = parseInt(v,0);
										if (w=="rotationZ") frm.rotationZ = parseInt(v,0);
										if (w=="rotationZ") frm.rotation = parseInt(v,0);
										if (w=="scaleX")  frm.scaleX = parseFloat(v);
										if (w=="scaleY")  frm.scaleY = parseFloat(v);
										if (w=="opacity") frm.opacity = parseFloat(v);
										if (w=="skewX")   frm.skewX = parseInt(v,0);
										if (w=="skewY")   frm.skewY = parseInt(v,0);
										if (w=="x") frm.x = parseInt(v,0);
										if (w=="y") frm.y = parseInt(v,0);
										if (w=="z") frm.z = parseInt(v,0);
										if (w=="transformOrigin") frm.transformOrigin = v.toString();
										if (w=="transformPerspective") frm.transformPerspective=parseInt(v,0);
									})

									return frm;
								}
				///////////////////////////////////////////////////////////////////
				// ANALYSE AND READ OUT DATAS FROM HTML CAPTIONS ANIMATION STEPS //
				///////////////////////////////////////////////////////////////////
				var getAnimSteps = function(data) {

						var paramarray = data.split("animation:");
						var params = new Object();

						params.animation = getAnimDatas(newAnimObject(),paramarray[1]);
						var customarray = paramarray[0].split(';');

						jQuery.each(customarray,function(index,param) {
							param = param.split(":")
							var w = param[0],
								v = param[1];
							if (w=="typ") params.typ = v;
							if (w=="speed") params.speed = parseInt(v,0)/1000;
							if (w=="start") params.start = parseInt(v,0)/1000;
							if (w=="elementdelay")  params.elementdelay = parseFloat(v);
							if (w=="ease")  params.ease = v;
						})

					return params;
				}




				////////////////////////
				// SHOW THE CAPTION  //
				///////////////////////
				var animateTheCaptions = function(nextli, opt,recalled,mtl) {

						// MAKE SURE THE ANIMATION ENDS WITH A CLEANING ON MOZ TRANSFORMS
						function animcompleted() {
						}

						function tlstart() {
						}

						if (nextli.data('ctl')==undefined) {
							nextli.data('ctl',new punchgs.TimelineLite());
						}

						var ctl = nextli.data('ctl'),
							offsetx=0,
							offsety=0,
							allcaptions = nextli.find('.tp-caption'),
							allstaticcaptions = opt.container.find('.tp-static-layers').find('.tp-caption');


						ctl.pause();

						jQuery.each(allstaticcaptions, function(index,staticcapt) {
							allcaptions.push(staticcapt);
						});

						allcaptions.each(function(i) {
								var internrecalled = recalled,
							    	staticdirection = -1,	// 1 -> In,  2-> Out  0-> Ignore  -1-> Not Static
									nextcaption=jQuery(this);

								if (nextcaption.hasClass("tp-static-layer")) {
										var nss = nextcaption.data('startslide'),
											nes = nextcaption.data('endslide');

									if ( nss == -1 || nss == "-1")
										nextcaption.data('startslide',0);

									if ( nes== -1 || nes == "-1")
										nextcaption.data('endslide',opt.slideamount);

									if (nss==0 && nes==opt.slideamount-1)
										nextcaption.data('endslide',opt.slideamount+1);


									// RESET SETTIGNS AFTER SETTING THEM AGAIN
									nss = nextcaption.data('startslide'),
									nes = nextcaption.data('endslide');


									// IF STATIC ITEM CURRENTLY NOT VISIBLE
									if (!nextcaption.hasClass("tp-is-shown")) {
										// IF ITEM SHOULD BECOME VISIBLE


										if ((nss<=opt.next && nes>=opt.next) ||
											(nss == opt.next) || (nes == opt.next)){

												nextcaption.addClass("tp-is-shown");
												staticdirection = 1;
										} else {

											staticdirection = 0;
										}
									// IF STATIC ITEM ALREADY VISIBLE
									} else {
										if ((nes==opt.next) ||
											(nss > opt.next) ||
											(nes < opt.next)) {

											staticdirection = 2;
											//nextcaption.removeClass("tp-is-shown");
										} else {
											staticdirection = 0;
										}

									}

									//if (staticdirection==2) staticdirection = 0;

								}

								offsetx = opt.width/2 - (opt.startwidth*opt.bw)/2;

								var xbw = opt.bw;
								var xbh = opt.bh;

								if (opt.fullScreen=="on")
									  offsety = opt.height/2 - (opt.startheight*opt.bh)/2;

								if (opt.autoHeight=="on" || (opt.minHeight!=undefined && opt.minHeight>0))
									  offsety = opt.container.height()/2 - (opt.startheight*opt.bh)/2;;


								if (offsety<0) offsety=0;



								var handlecaption=0;

								// HIDE CAPTION IF RESOLUTION IS TOO LOW
								if (opt.width<opt.hideCaptionAtLimit && nextcaption.data('captionhidden')=="on") {
									nextcaption.addClass("tp-hidden-caption")
									handlecaption=1;
								} else {
									if (opt.width<opt.hideAllCaptionAtLimit || opt.width<opt.hideAllCaptionAtLilmit)	{
										nextcaption.addClass("tp-hidden-caption")
										handlecaption=1;
									} else {
										nextcaption.removeClass("tp-hidden-caption")
									}
								}



								if (handlecaption==0) {

									// ADD A CLICK LISTENER TO THE CAPTION
									if (nextcaption.data('linktoslide')!=undefined && !nextcaption.hasClass("hasclicklistener")) {
										nextcaption.addClass("hasclicklistener")
										nextcaption.css({'cursor':'pointer'});
										if (nextcaption.data('linktoslide')!="no") {
											nextcaption.click(function() {
												var nextcaption=jQuery(this);
												var dir = nextcaption.data('linktoslide');
												if (dir!="next" && dir!="prev") {
													opt.container.data('showus',dir);
													opt.container.parent().find('.tp-rightarrow').click();
												} else
													if (dir=="next")
														opt.container.parent().find('.tp-rightarrow').click();
												else
													if (dir=="prev")
														opt.container.parent().find('.tp-leftarrow').click();
											});
										}
									}// END OF CLICK LISTENER


									if (offsetx<0) offsetx=0;


									if (nextcaption.hasClass("tp-videolayer") || nextcaption.find('iframe').length>0 || nextcaption.find('video').length>0 ) {

										// YOUTUBE AND VIMEO LISTENRES INITIALISATION
										var frameID = "iframe"+Math.round(Math.random()*100000+1),
											vidw = nextcaption.data("videowidth"),
											vidh = nextcaption.data("videoheight"),
											vida = nextcaption.data("videoattributes"),
											vidytid = nextcaption.data('ytid'),
											vimeoid = nextcaption.data('vimeoid'),
											videopreload = nextcaption.data('videpreload'),
											videomp = nextcaption.data('videomp4'),
											videowebm = nextcaption.data('videowebm'),
											videoogv = nextcaption.data('videoogv'),
											videocontrols = nextcaption.data('videocontrols'),
											httpprefix = "http",
											videoloop = nextcaption.data('videoloop')=="loop" ? "loop" : nextcaption.data('videoloop')=="loopandnoslidestop" ? "loop" : "";

										if (nextcaption.data('thumbimage')!=undefined && nextcaption.data('videoposter')==undefined)
											nextcaption.data('videoposter',nextcaption.data('thumbimage'))

										// ADD YOUTUBE IFRAME IF NEEDED
										if (vidytid!=undefined && String(vidytid).length>1 && nextcaption.find('iframe').length==0) {
											httpprefix = "https";

											if (videocontrols=="none") {
										 		vida = vida.replace("controls=1","controls=0");
										 		if (vida.toLowerCase().indexOf('controls')==-1)
										 		  vida = vida+"&controls=0";
										 	}
											nextcaption.append('<iframe style="visible:hidden" src="'+httpprefix+'://www.youtube.com/embed/'+vidytid+'?'+vida+'" width="'+vidw+'" height="'+vidh+'" style="width:'+vidw+'px;height:'+vidh+'px"></iframe>');
										}

										// ADD VIMEO IFRAME IF NEEDED
										if (vimeoid!=undefined && String(vimeoid).length>1 && nextcaption.find('iframe').length==0) {
											if (location.protocol === 'https:')
												httpprefix = "https";

											nextcaption.append('<iframe style="visible:hidden" src="'+httpprefix+'://player.vimeo.com/video/'+vimeoid+'?'+vida+'" width="'+vidw+'" height="'+vidh+'" style="width:'+vidw+'px;height:'+vidh+'px"></iframe>');
										}

										// ADD HTML5 VIDEO IF NEEDED
										if ((videomp!=undefined || videowebm!=undefined) && nextcaption.find('video').length==0) {

											if (videocontrols!="controls") videocontrols="";
											var apptxt = '<video style="visible:hidden" class="" '+videoloop+' preload="'+videopreload+'" width="'+vidw+'" height="'+vidh+'"';
											/*if (nextcaption.data('videoposter')!=undefined)
												apptxt = apptxt + 'poster="'+nextcaption.data('videoposter')+'">';
												apptxt = apptxt + '<source src="'+videomp+'" type="video/mp4" />';
												apptxt = apptxt + '<source src="'+videowebm+'" type="video/webm" />';
												apptxt = apptxt + '<source src="'+videoogv+'" type="video/ogg" />';
												apptxt = apptxt + '</video>';
											nextcaption.append(apptxt);*/
											
											if (nextcaption.data('videoposter')!=undefined)
												if (nextcaption.data('videoposter') != undefined) apptxt = apptxt + 'poster="'+nextcaption.data('videoposter')+'">';
												if (videowebm!=undefined && get_browser().toLowerCase()=="firefox") apptxt = apptxt + '<source src="'+videowebm+'" type="video/webm" />';
												if (videomp!=undefined) apptxt = apptxt + '<source src="'+videomp+'" type="video/mp4" />';
												if (videoogv!=undefined) apptxt = apptxt + '<source src="'+videoogv+'" type="video/ogg" />';
												apptxt = apptxt + '</video>';
											nextcaption.append(apptxt);

											if (videocontrols=="controls")
												nextcaption.append('<div class="tp-video-controls">'+
																		'<div class="tp-video-button-wrap"><button type="button" class="tp-video-button tp-vid-play-pause">Play</button></div>'+
																		'<div class="tp-video-seek-bar-wrap"><input  type="range" class="tp-seek-bar" value="0"></div>'+
																		'<div class="tp-video-button-wrap"><button  type="button" class="tp-video-button tp-vid-mute">Mute</button></div>'+
																		'<div class="tp-video-vol-bar-wrap"><input  type="range" class="tp-volume-bar" min="0" max="1" step="0.1" value="1"></div>'+
																		'<div class="tp-video-button-wrap"><button  type="button" class="tp-video-button tp-vid-full-screen">Full-Screen</button></div>'+
																	'</div>');
										}

										// RESET DEFAULTS
										var autoplaywason = false;
										if (nextcaption.data('autoplayonlyfirsttime') == true || nextcaption.data('autoplayonlyfirsttime')=="true" || nextcaption.data('autoplay')==true) {
											nextcaption.data('autoplay',true);
											autoplaywason = true;
										}


										nextcaption.find('iframe').each(function() {
												var ifr=jQuery(this);

												punchgs.TweenLite.to(ifr,0.1,{autoAlpha:1, zIndex:0, transformStyle:"preserve-3d",z:0,rotationX:0,force3D:"auto"});
												if (is_mobile()) {
													var oldsrc = ifr.attr('src');
													ifr.attr('src',"");
													ifr.attr('src',oldsrc);
												}


												// START YOUTUBE HANDLING
												opt.nextslideatend = nextcaption.data('nextslideatend');

												// IF VIDEOPOSTER EXISTING
												if (nextcaption.data('videoposter')!=undefined && nextcaption.data('videoposter').length>2 && nextcaption.data('autoplay')!=true && !internrecalled) {
													if (nextcaption.find('.tp-thumb-image').length==0)
														nextcaption.append('<div class="tp-thumb-image" style="cursor:pointer; position:absolute;top:0px;left:0px;width:100%;height:100%;background-image:url('+nextcaption.data('videoposter')+'); background-size:cover"></div>');
													else
													  punchgs.TweenLite.set(nextcaption.find('.tp-thumb-image'),{autoAlpha:1});
												}

												// IF IFRAME IS A YOUTUBE FRAME
												if (ifr.attr('src').toLowerCase().indexOf('youtube')>=0) {

														// IF LISTENER DOES NOT EXIST YET
														 if (!ifr.hasClass("HasListener")) {
															try {
																ifr.attr('id',frameID);
																var player;
																var ytint = setInterval(function() {
																	if (YT !=undefined)
																		if (typeof YT.Player != undefined && typeof YT.Player !="undefined") {
																			player = new YT.Player(frameID, {
																				events: {
																					"onStateChange": onPlayerStateChange,
																					'onReady': function(event) {
																						var embedCode = event.target.getVideoEmbedCode(),
																							ytcont = jQuery('#'+embedCode.split('id="')[1].split('"')[0]),
																							nextcaption = ytcont.closest('.tp-caption'),
																							videorate = nextcaption.data('videorate'),
																							videostart = nextcaption.data('videostart');


																						if (videorate!=undefined)
																							event.target.setPlaybackRate(parseFloat(videorate));

																						/*if (nextcaption.data('autoplay')==true || autoplaywason)
																							event.target.playVideo();*/

																						if (!is_mobile() && nextcaption.data('autoplay')==true || autoplaywason) {
																								nextcaption.data('timerplay',setTimeout(function() {
																									event.target.playVideo();
																								},nextcaption.data('start')));
																						}

																						// PLAY VIDEO IF THUMBNAIL HAS BEEN CLICKED
																						 nextcaption.find('.tp-thumb-image').click(function() {
																							 punchgs.TweenLite.to(jQuery(this),0.3,{autoAlpha:0,force3D:"auto",ease:punchgs.Power3.easeInOut})
																							 if (!is_mobile()) {
																								 player.playVideo();
																							}
																						 })

																					}
																				}
																			});
																		}
																		ifr.addClass("HasListener");
																		nextcaption.data('player',player);
																		clearInterval(ytint);
																}, 100)
															} catch(e) {}
													 } else {
													 	if (!recalled) {
														 	var player=nextcaption.data('player');
															if (nextcaption.data('forcerewind')=="on" && !is_mobile())
																	player.seekTo(0);

															if (!is_mobile() && nextcaption.data('autoplay')==true || autoplaywason) {
																	nextcaption.data('timerplay',setTimeout(function() {
																		player.playVideo();
																	},nextcaption.data('start')));
															}
														}
													 } // END YOUTUBE HANDLING


												} else

												// START VIMEO HANDLING
												if (ifr.attr('src').toLowerCase().indexOf('vimeo')>=0) {
														   if (!ifr.hasClass("HasListener")) {
																ifr.addClass("HasListener");
																ifr.attr('id',frameID);
																var isrc = ifr.attr('src');
																var queryParameters = {}, queryString = isrc,
																re = /([^&=]+)=([^&]*)/g, m;
																// Creates a map with the query string parameters
																while (m = re.exec(queryString)) {
																	queryParameters[decodeURIComponent(m[1])] = decodeURIComponent(m[2]);
																}

																if (queryParameters['player_id']!=undefined)
																	isrc = isrc.replace(queryParameters['player_id'],frameID);
																else
																	isrc=isrc+"&player_id="+frameID;

																try{ isrc = isrc.replace('api=0','api=1'); } catch(e) {}

																isrc=isrc+"&api=1";

																ifr.attr('src',isrc);
																var player = nextcaption.find('iframe')[0];
																var vimint = setInterval(function() {
																	if ($f !=undefined){
																		if (typeof $f(frameID).api != undefined && typeof $f(frameID).api !="undefined") {

																			$f(player).addEvent('ready', function(){
																				vimeoready_auto(frameID,autoplaywason)
																			});
																			clearInterval(vimint);
																		}
																	}
																},100);

															 } else {
															 		if (!recalled) {
																		if (!is_mobile() && (nextcaption.data('autoplay')==true || nextcaption.data('forcerewind')=="on")) {

																			var ifr = nextcaption.find('iframe');
																			var id = ifr.attr('id');
																			var froogaloop = $f(id);
																			if (nextcaption.data('forcerewind')=="on")
																					froogaloop.api("seekTo",0);
																			nextcaption.data('timerplay',setTimeout(function() {
																				if (nextcaption.data('autoplay')==true)
																					froogaloop.api("play");
																			},nextcaption.data('start')));
																		}
																	}
															 }// END HAS LISTENER HANDLING
												}  // END OF VIMEO HANDLING
										}); // END OF LOOP THROUGH IFRAMES



										// START OF HTML5 VIDEOS
										if ((is_mobile() && nextcaption.data('disablevideoonmobile')==1) ||isIE(8)) nextcaption.find('video').remove();
										//if (is_mobile() && jQuery(window).width()<569)  nextcaption.find('video').remove()

										if (nextcaption.find('video').length>0) {
											nextcaption.find('video').each(function(i) {

												var video = this,
													jvideo = jQuery(this);


												if (!jvideo.parent().hasClass("html5vid"))
													jvideo.wrap('<div class="html5vid" style="position:relative;top:0px;left:0px;width:auto;height:auto"></div>');

												var html5vid = jvideo.parent();

												// WAITING FOR META DATAS

												addEvent(video,'loadedmetadata',function(html5vid) {
														html5vid.data('metaloaded',1);
												}(html5vid));


												clearInterval(html5vid.data('interval'));
												html5vid.data('interval',setInterval(function() {
													if (html5vid.data('metaloaded')==1 || video.duration!=NaN) {
														clearInterval(html5vid.data('interval'));
														// FIRST TIME LOADED THE HTML5 VIDEO
														if (!html5vid.hasClass("HasListener")) {
																html5vid.addClass("HasListener");

																if (nextcaption.data('dottedoverlay')!="none" && nextcaption.data('dottedoverlay')!=undefined)
																if (nextcaption.find('.tp-dottedoverlay').length!=1)
																	html5vid.append('<div class="tp-dottedoverlay '+nextcaption.data('dottedoverlay')+'"></div>');

																if (jvideo.attr('control') == undefined ) {
																	if (html5vid.find('.tp-video-play-button').length==0)
																		html5vid.append('<div class="tp-video-play-button"><i class="revicon-right-dir"></i><div class="tp-revstop"></div></div>');
																	html5vid.find('video, .tp-poster, .tp-video-play-button').click(function() {
																		if (html5vid.hasClass("videoisplaying"))
																			video.pause();
																		else
																			video.play();
																	})
																}

																if (nextcaption.data('forcecover')==1 || nextcaption.hasClass('fullscreenvideo'))  {
																	if (nextcaption.data('forcecover')==1) {
																		updateHTML5Size(html5vid,opt.container);
																		html5vid.addClass("fullcoveredvideo");
																		nextcaption.addClass("fullcoveredvideo");
																	}
																	html5vid.css({width:"100%", height:"100%"});
																}



																var playButton = nextcaption.find('.tp-vid-play-pause')[0],
																	muteButton = nextcaption.find('.tp-vid-mute')[0],
																	fullScreenButton = nextcaption.find('.tp-vid-full-screen')[0],
																	seekBar = nextcaption.find('.tp-seek-bar')[0],
																	volumeBar = nextcaption.find('.tp-volume-bar')[0];

																if (playButton!=undefined) {
																	// Event listener for the play/pause button
																	addEvent(playButton,"click", function() {
																		if (video.paused == true)
																			// Play the video
																			video.play();
																		else
																			// Pause the video
																			video.pause();
																	});

																	// Event listener for the mute button
																	addEvent(muteButton,"click", function() {
																		if (video.muted == false) {
																			// Mute the video
																			video.muted = true;

																			// Update the button text
																			muteButton.innerHTML = "Unmute";
																		} else {
																			// Unmute the video
																			video.muted = false;

																			// Update the button text
																			muteButton.innerHTML = "Mute";
																		}
																	});

																	// Event listener for the full-screen button
																	addEvent(fullScreenButton,"click", function() {
																		if (video.requestFullscreen) {
																			video.requestFullscreen();
																		} else if (video.mozRequestFullScreen) {
																			video.mozRequestFullScreen(); // Firefox
																		} else if (video.webkitRequestFullscreen) {
																			video.webkitRequestFullscreen(); // Chrome and Safari
																		}
																	});


																	// Event listener for the seek bar
																	addEvent(seekBar,"change", function() {
																		// Calculate the new time
																		var time = video.duration * (seekBar.value / 100);
																		// Update the video time
																		video.currentTime = time;
																	});


																	// Update the seek bar as the video plays
																	addEvent(video,"timeupdate", function() {
																		// Calculate the slider value
																		var value = (100 / video.duration) * video.currentTime;

																		// Update the slider value
																		seekBar.value = value;
																	});

																	// Pause the video when the seek handle is being dragged
																	addEvent(seekBar,"mousedown", function() {
																		video.pause();
																	});

																	// Play the video when the seek handle is dropped
																	addEvent(seekBar,"mouseup", function() {
																		video.play();
																	});

																	// Event listener for the volume bar
																	addEvent(volumeBar,"change", function() {
																		// Update the video volume
																		video.volume = volumeBar.value;
																	});
																}


																// VIDEO EVENT LISTENER FOR "PLAY"
																addEvent(video,"play",function() {
																		if (nextcaption.data('volume')=="mute")
																			  video.muted=true;

																		html5vid.addClass("videoisplaying");

			 															if (nextcaption.data('videoloop')=="loopandnoslidestop") {
																			opt.videoplaying=false;
																			opt.container.trigger('starttimer');
																			opt.container.trigger('revolution.slide.onvideostop');
																		} else {

																			opt.videoplaying=true;
																			opt.container.trigger('stoptimer');
																			opt.container.trigger('revolution.slide.onvideoplay');
																		}

																		var playButton = nextcaption.find('.tp-vid-play-pause')[0],
																			muteButton = nextcaption.find('.tp-vid-mute')[0];
																		if (playButton!=undefined)
																			playButton.innerHTML = "Pause";
																		if (muteButton!=undefined && video.muted)
																			muteButton.innerHTML = "Unmute";
																	});

																// VIDEO EVENT LISTENER FOR "PAUSE"
																addEvent(video,"pause",function() {
																			html5vid.removeClass("videoisplaying");
																			opt.videoplaying=false;
																			opt.container.trigger('starttimer');
																			opt.container.trigger('revolution.slide.onvideostop');
																			var playButton = nextcaption.find('.tp-vid-play-pause')[0];
																			if (playButton!=undefined)
																				playButton.innerHTML = "Play";

																	});

																// VIDEO EVENT LISTENER FOR "END"
																addEvent(video,"ended",function() {
																			html5vid.removeClass("videoisplaying");
																			opt.videoplaying=false;
																			opt.container.trigger('starttimer');
																			opt.container.trigger('revolution.slide.onvideostop');
																			if (opt.nextslideatend==true)
																				opt.container.revnext();
																	});

															} // END OF LISTENER DECLARATION

															var autoplaywason = false;
															if (nextcaption.data('autoplayonlyfirsttime') == true || nextcaption.data('autoplayonlyfirsttime')=="true")
																autoplaywason = true;

															var mediaaspect=16/9;
															if (nextcaption.data('aspectratio')=="4:3") mediaaspect=4/3;
															html5vid.data('mediaAspect',mediaaspect);

															if (html5vid.closest('.tp-caption').data('forcecover')==1) {
																updateHTML5Size(html5vid,opt.container);
																html5vid.addClass("fullcoveredvideo");
															}

															jvideo.css({display:"block"});
															opt.nextslideatend = nextcaption.data('nextslideatend');

															// IF VIDEO SHOULD BE AUTOPLAYED
															if (nextcaption.data('autoplay')==true || autoplaywason==true) {


																if (nextcaption.data('videoloop')=="loopandnoslidestop") {
																	opt.videoplaying=false;
																	opt.container.trigger('starttimer');
																	opt.container.trigger('revolution.slide.onvideostop');
																} else {
																	opt.videoplaying=true;
																	opt.container.trigger('stoptimer');
																	opt.container.trigger('revolution.slide.onvideoplay');
																}


																if (nextcaption.data('forcerewind')=="on" && !html5vid.hasClass("videoisplaying"))
																	if (video.currentTime>0) video.currentTime=0;

																if (nextcaption.data('volume')=="mute")
																	video.muted = true;

																html5vid.data('timerplay',setTimeout(function() {

																	if (nextcaption.data('forcerewind')=="on" && !html5vid.hasClass("videoisplaying"))
																		if (video.currentTime>0) video.currentTime=0;

																	if (nextcaption.data('volume')=="mute")
																			video.muted = true;


																		video.play();
																},10+nextcaption.data('start')));
															}

															if (html5vid.data('ww') == undefined) html5vid.data('ww',jvideo.attr('width'));
															if (html5vid.data('hh') == undefined) html5vid.data('hh',jvideo.attr('height'));

															if (!nextcaption.hasClass("fullscreenvideo") && nextcaption.data('forcecover')==1) {
																try{
																	html5vid.width(html5vid.data('ww')*opt.bw);
																	html5vid.height(html5vid.data('hh')*opt.bh);
																} catch(e) {}
															}

															clearInterval(html5vid.data('interval'));
													}
												}),100); // END OF SET INTERVAL

											});
										} // END OF HTML5 VIDEO FUNCTIONS

										// IF AUTOPLAY IS ON, WE NEED SOME STOP FUNCTION ON
										if (nextcaption.data('autoplay')==true) {
											setTimeout(function() {

												if (nextcaption.data('videoloop')!="loopandnoslidestop") {
													opt.videoplaying=true;
													opt.container.trigger('stoptimer');
												}
											},200)
											if (nextcaption.data('videoloop')!="loopandnoslidestop") {
												opt.videoplaying=true;
												opt.container.trigger('stoptimer');
											}

											if (nextcaption.data('autoplayonlyfirsttime') == true || nextcaption.data('autoplayonlyfirsttime')=="true" ) {
												nextcaption.data('autoplay',false);
												nextcaption.data('autoplayonlyfirsttime',false);
											}
										}
									}




									// NEW ENGINE
									//if (nextcaption.hasClass("randomrotate") && (opt.ie || opt.ie9)) nextcaption.removeClass("randomrotate").addClass("sfb");
									//	nextcaption.removeClass('noFilterClass');



								    var imw =0;
								    var imh = 0;

									if (nextcaption.find('img').length>0) {
														var im = nextcaption.find('img');
														if (im.width()==0) im.css({width:"auto"});
														if (im.height()==0) im.css({height:"auto"});

														if (im.data('ww') == undefined && im.width()>0) im.data('ww',im.width());
														if (im.data('hh') == undefined && im.height()>0) im.data('hh',im.height());

														var ww = im.data('ww');
														var hh = im.data('hh');

														if (ww==undefined) ww=0;
														if (hh==undefined) hh=0;

														im.width(ww*opt.bw);
														im.height(hh*opt.bh);
														imw = im.width();
														imh = im.height();
									} else {

									if (nextcaption.find('iframe').length>0 || nextcaption.find('video').length>0) {

															var html5vid = false,
																im = nextcaption.find('iframe');
															if (im.length==0) {
																	im = nextcaption.find('video');
																	html5vid = true;
															}
															im.css({display:"block"});

															if (nextcaption.data('ww') == undefined) nextcaption.data('ww',im.width());
															if (nextcaption.data('hh') == undefined) nextcaption.data('hh',im.height());

															var ww = nextcaption.data('ww'),
																hh = nextcaption.data('hh');

															var nc =nextcaption;
																if (nc.data('fsize') == undefined) nc.data('fsize',parseInt(nc.css('font-size'),0) || 0);
																if (nc.data('pt') == undefined) nc.data('pt',parseInt(nc.css('paddingTop'),0) || 0);
																if (nc.data('pb') == undefined) nc.data('pb',parseInt(nc.css('paddingBottom'),0) || 0);
																if (nc.data('pl') == undefined) nc.data('pl',parseInt(nc.css('paddingLeft'),0) || 0);
																if (nc.data('pr') == undefined) nc.data('pr',parseInt(nc.css('paddingRight'),0) || 0);

																if (nc.data('mt') == undefined) nc.data('mt',parseInt(nc.css('marginTop'),0) || 0);
																if (nc.data('mb') == undefined) nc.data('mb',parseInt(nc.css('marginBottom'),0) || 0);
																if (nc.data('ml') == undefined) nc.data('ml',parseInt(nc.css('marginLeft'),0) || 0);
																if (nc.data('mr') == undefined) nc.data('mr',parseInt(nc.css('marginRight'),0) || 0);

																if (nc.data('bt') == undefined) nc.data('bt',parseInt(nc.css('borderTop'),0) || 0);
																if (nc.data('bb') == undefined) nc.data('bb',parseInt(nc.css('borderBottom'),0) || 0);
																if (nc.data('bl') == undefined) nc.data('bl',parseInt(nc.css('borderLeft'),0) || 0);
																if (nc.data('br') == undefined) nc.data('br',parseInt(nc.css('borderRight'),0) || 0);

																if (nc.data('lh') == undefined) nc.data('lh',parseInt(nc.css('lineHeight'),0) || 0);

																// IE8 FIX FOR AUTO LINEHEIGHT
																if (nc.data('lh')=="auto") nc.data('lh',nc.data('fsize')+4);

																var fvwidth=opt.width,
																	fvheight=opt.height;
																if (fvwidth>opt.startwidth) fvwidth=opt.startwidth;
																if (fvheight>opt.startheight) fvheight=opt.startheight;

																if (!nextcaption.hasClass('fullscreenvideo'))
																			nextcaption.css({

																				 'font-size': (nc.data('fsize') * opt.bw)+"px",

																				 'padding-top': (nc.data('pt') * opt.bh) + "px",
																				 'padding-bottom': (nc.data('pb') * opt.bh) + "px",
																				 'padding-left': (nc.data('pl') * opt.bw) + "px",
																				 'padding-right': (nc.data('pr') * opt.bw) + "px",

																				 'margin-top': (nc.data('mt') * opt.bh) + "px",
																				 'margin-bottom': (nc.data('mb') * opt.bh) + "px",
																				 'margin-left': (nc.data('ml') * opt.bw) + "px",
																				 'margin-right': (nc.data('mr') * opt.bw) + "px",

																				 'border-top': (nc.data('bt') * opt.bh) + "px",
																				 'border-bottom': (nc.data('bb') * opt.bh) + "px",
																				 'border-left': (nc.data('bl') * opt.bw) + "px",
																				 'border-right': (nc.data('br') * opt.bw) + "px",

																				 'line-height': (nc.data('lh') * opt.bh) + "px",
																				 'height':(hh*opt.bh)+'px'
																				});
																	else  {

																		   offsetx=0; offsety=0;
																		   nextcaption.data('x',0)
																		   nextcaption.data('y',0)

																		   var ovhh = opt.height
																		   if (opt.autoHeight=="on")
																		   		ovhh = opt.container.height()
																			nextcaption.css({

																				'width':opt.width,
																				'height':ovhh
																			});
																		}

															if (html5vid == false) {
																im.width(ww*opt.bw);
																im.height(hh*opt.bh);
															}

															else

															if (nextcaption.data('forcecover')!=1 && !nextcaption.hasClass('fullscreenvideo')) {
																im.width(ww*opt.bw);
																im.height(hh*opt.bh);
															}


															imw = im.width();
															imh = im.height();
														}

											else {


												nextcaption.find('.tp-resizeme, .tp-resizeme *').each(function() {
														calcCaptionResponsive(jQuery(this),opt);
												});

												if (nextcaption.hasClass("tp-resizeme")) {
													nextcaption.find('*').each(function() {
														calcCaptionResponsive(jQuery(this),opt);
													});
												}

												calcCaptionResponsive(nextcaption,opt);

												imh=nextcaption.outerHeight(true);
												imw=nextcaption.outerWidth(true);

												// NEXTCAPTION FRONTCORNER CHANGES
												var ncch = nextcaption.outerHeight();
												var bgcol = nextcaption.css('backgroundColor');
												nextcaption.find('.frontcorner').css({
																'borderWidth':ncch+"px",
																'left':(0-ncch)+'px',
																'borderRight':'0px solid transparent',
																'borderTopColor':bgcol
												});

												nextcaption.find('.frontcornertop').css({
																'borderWidth':ncch+"px",
																'left':(0-ncch)+'px',
																'borderRight':'0px solid transparent',
																'borderBottomColor':bgcol
												});

												// NEXTCAPTION BACKCORNER CHANGES
												nextcaption.find('.backcorner').css({
																'borderWidth':ncch+"px",
																'right':(0-ncch)+'px',
																'borderLeft':'0px solid transparent',
																'borderBottomColor':bgcol
												});

												// NEXTCAPTION BACKCORNER CHANGES
												nextcaption.find('.backcornertop').css({
																'borderWidth':ncch+"px",
																'right':(0-ncch)+'px',
																'borderLeft':'0px solid transparent',
																'borderTopColor':bgcol
												});

											 }


									}

									if (opt.fullScreenAlignForce == "on") {
										//xbw = 1;
										//xbh = 1;
										offsetx=0;
										offsety=0;
									}



									if (nextcaption.data('voffset')==undefined) nextcaption.data('voffset',0);
									if (nextcaption.data('hoffset')==undefined) nextcaption.data('hoffset',0);

									var vofs= nextcaption.data('voffset')*xbw;
									var hofs= nextcaption.data('hoffset')*xbw;

									var crw = opt.startwidth*xbw;
									var crh = opt.startheight*xbw;

									if (opt.fullScreenAlignForce == "on") {
										crw = opt.container.width();
										crh = opt.container.height();
									}



									// CENTER THE CAPTION HORIZONTALLY
									if (nextcaption.data('x')=="center" || nextcaption.data('xcenter')=='center') {
										nextcaption.data('xcenter','center');
										//nextcaption.data('x',(crw/2 - nextcaption.outerWidth(true)/2)/xbw+  hofs);
										nextcaption.data('x',(crw/2 - nextcaption.outerWidth(true)/2) +  hofs);


									}

									// ALIGN LEFT THE CAPTION HORIZONTALLY
									if (nextcaption.data('x')=="left" || nextcaption.data('xleft')=='left') {
										nextcaption.data('xleft','left');

										nextcaption.data('x',(0)/xbw+hofs);

									}

									// ALIGN RIGHT THE CAPTION HORIZONTALLY
									if (nextcaption.data('x')=="right" || nextcaption.data('xright')=='right') {
										nextcaption.data('xright','right');
										nextcaption.data('x',((crw - nextcaption.outerWidth(true))+hofs)/xbw);
										//konsole.log("crw:"+crw+"  width:"+nextcaption.outerWidth(true)+"  xbw:"+xbw);
										//konsole.log("x-pos:"+nextcaption.data('x'))
									}


									// CENTER THE CAPTION VERTICALLY
									if (nextcaption.data('y')=="center" || nextcaption.data('ycenter')=='center') {
										nextcaption.data('ycenter','center');
										nextcaption.data('y',(crh/2 - nextcaption.outerHeight(true)/2) + vofs);
									}

									// ALIGN TOP THE CAPTION VERTICALLY
									if (nextcaption.data('y')=="top" || nextcaption.data('ytop')=='top') {
										nextcaption.data('ytop','top');
										nextcaption.data('y',(0)/opt.bh+vofs);

									}

									// ALIGN BOTTOM THE CAPTION VERTICALLY
									if (nextcaption.data('y')=="bottom" || nextcaption.data('ybottom')=='bottom') {
										nextcaption.data('ybottom','bottom');
										nextcaption.data('y',((crh - nextcaption.outerHeight(true))+vofs)/xbw);

									}



									// THE TRANSITIONS OF CAPTIONS
									// MDELAY AND MSPEED
									if (nextcaption.data('start') == undefined) nextcaption.data('start',1000);



									var easedata=nextcaption.data('easing');
									if (easedata==undefined) easedata="punchgs.Power1.easeOut";


									var mdelay = nextcaption.data('start')/1000,
										mspeed = nextcaption.data('speed')/1000;


									if (nextcaption.data('x')=="center" || nextcaption.data('xcenter')=='center')
										var calcx = (nextcaption.data('x')+offsetx);
									else {

										var calcx = (xbw*nextcaption.data('x')+offsetx);
									}


									if (nextcaption.data('y')=="center" || nextcaption.data('ycenter')=='center')
										var calcy = (nextcaption.data('y')+offsety);
									else {
										//if (opt.fullScreenAlignForce == "on" && (nextcaption.data('y')=="bottom" || nextcaption.data('ybottom')=='bottom'))
										//	opt.bh = 1;

										var calcy = (opt.bh*nextcaption.data('y')+offsety);
									}


							punchgs.TweenLite.set(nextcaption,{top:calcy,left:calcx,overwrite:"auto"});

							if (staticdirection == 0)
								internrecalled = true;

							if (nextcaption.data('timeline')!=undefined && !internrecalled) {
								if (staticdirection!=2)
									nextcaption.data('timeline').gotoAndPlay(0);
								internrecalled = true;
							}

							if (!internrecalled) {



									// CLEAR THE TIMELINE, SINCE IT CAN BE DAMAGED, OR PAUSED AT A FEW PART
									if (nextcaption.data('timeline')!=undefined) {
										//nextcaption.data('timeline').clear();
									 }

									var tl = new punchgs.TimelineLite({smoothChildTiming:true,onStart:tlstart});
									tl.pause();


									if (opt.fullScreenAlignForce == "on") {
										//calcy = nextcaption.data('y')+offsety;
									}

									var animobject = nextcaption;
									if (nextcaption.data('mySplitText') !=undefined) nextcaption.data('mySplitText').revert();


									if (nextcaption.data('splitin') == "chars" || nextcaption.data('splitin') == "words" || nextcaption.data('splitin') == "lines" || nextcaption.data('splitout') == "chars" || nextcaption.data('splitout') == "words" || nextcaption.data('splitout') == "lines") {
										if (nextcaption.find('a').length>0)
											nextcaption.data('mySplitText',new punchgs.SplitText(nextcaption.find('a'),{type:"lines,words,chars",charsClass:"tp-splitted",wordsClass:"tp-splitted",linesClass:"tp-splitted"}));
										else
										if (nextcaption.find('.tp-layer-inner-rotation').length>0)
											nextcaption.data('mySplitText',new punchgs.SplitText(nextcaption.find('.tp-layer-inner-rotation'),{type:"lines,words,chars",charsClass:"tp-splitted",wordsClass:"tp-splitted",linesClass:"tp-splitted"}));
										else
											nextcaption.data('mySplitText',new punchgs.SplitText(nextcaption,{type:"lines,words,chars",charsClass:"tp-splitted",wordsClass:"tp-splitted",linesClass:"tp-splitted"}));

										nextcaption.addClass("splitted");
									}

									if (nextcaption.data('splitin') == "chars")
										animobject = nextcaption.data('mySplitText').chars;


									if (nextcaption.data('splitin') == "words")
										animobject = nextcaption.data('mySplitText').words;


									if (nextcaption.data('splitin') == "lines")
										animobject = nextcaption.data('mySplitText').lines;



									var frm = newAnimObject();
									var endfrm = newAnimObject();


									if (nextcaption.data('repeat')!=undefined) repeatV = nextcaption.data('repeat');
									if (nextcaption.data('yoyo')!=undefined) yoyoV = nextcaption.data('yoyo');
									if (nextcaption.data('repeatdelay')!=undefined) repeatdelayV = nextcaption.data('repeatdelay');

									var ncc = nextcaption.attr('class');

									// WHICH ANIMATION TYPE SHOULD BE USED
									if (ncc.match("customin")) frm = getAnimDatas(frm,nextcaption.data('customin'));
									else
									if (ncc.match("randomrotate")) {

												frm.scale = Math.random()*3+1;
												frm.rotation = Math.round(Math.random()*200-100);
												frm.x = Math.round(Math.random()*200-100);
												frm.y = Math.round(Math.random()*200-100);
									}
									else
									if (ncc.match('lfr') || ncc.match('skewfromright')) frm.x = 15+opt.width;
									else
									if (ncc.match('lfl') || ncc.match('skewfromleft')) frm.x = -15-imw;
									else
									if (ncc.match('sfl') || ncc.match('skewfromleftshort')) frm.x = -50;
									else
									if (ncc.match('sfr') || ncc.match('skewfromrightshort')) frm.x = 50;
									else
									if (ncc.match('lft')) frm.y = -25 - imh;
									else
									if (ncc.match('lfb')) frm.y = 25 + opt.height;
									else
									if (ncc.match('sft')) frm.y = -50;
									else
									if (ncc.match('sfb')) frm.y = 50;


									if (ncc.match('skewfromright') || nextcaption.hasClass('skewfromrightshort')) frm.skewX = -85
									else
									if (ncc.match('skewfromleft') || nextcaption.hasClass('skewfromleftshort')) frm.skewX =  85


									if (ncc.match("fade") || ncc.match('sft') || ncc.match('sfl') || ncc.match('sfb') || ncc.match('skewfromleftshort')  || ncc.match('sfr') || ncc.match('skewfromrightshort'))
										frm.opacity = 0;

									// FOR SAFARI WE NEED TO REMOVE 3D ROTATIONS
									if (get_browser().toLowerCase()=="safari") {
										//frm.rotationX=0;frm.rotationY=0;
									}

									var elemdelay = (nextcaption.data('elementdelay') == undefined) ? 0 : nextcaption.data('elementdelay');
									endfrm.ease = frm.ease = (nextcaption.data('easing') == undefined) ? punchgs.Power1.easeInOut : nextcaption.data('easing');


									// DISTANCES SHOULD BE RESIZED ALSO

									frm.data = new Object();
									frm.data.oldx = frm.x;
									frm.data.oldy = frm.y;

									endfrm.data = new Object();
									endfrm.data.oldx = endfrm.x;
									endfrm.data.oldy = endfrm.y;

									frm.x = frm.x * xbw;
									frm.y = frm.y * xbw;

									var newtl = new punchgs.TimelineLite();


									if (staticdirection != 2) {

										// CHANGE to punchgs.TweenLite.  if Yoyo and Repeat is used. Dont forget to laod the Right Tools for it !!
										if (ncc.match("customin")) {
											  if (animobject != nextcaption)
												  tl.add(punchgs.TweenLite.set(nextcaption, { force3D:"auto",opacity:1,scaleX:1,scaleY:1,rotationX:0,rotationY:0,rotationZ:0,skewX:0,skewY:0,z:0,x:0,y:0,visibility:'visible',delay:0,overwrite:"all"}));
											  frm.visibility = "hidden";
											  endfrm.visibility = "visible";
											  endfrm.overwrite = "all";
											  endfrm.opacity = 1;
											  endfrm.onComplete = animcompleted();
											  endfrm.delay = mdelay;
											  endfrm.force3D="auto"

											  tl.add(newtl.staggerFromTo(animobject,mspeed,frm,endfrm,elemdelay),"frame0");

										} else {

												frm.visibility = "visible";
												frm.transformPerspective = 600;
												if (animobject != nextcaption)
												  tl.add(punchgs.TweenLite.set(nextcaption, { force3D:"auto",opacity:1,scaleX:1,scaleY:1,rotationX:0,rotationY:0,rotationZ:0,skewX:0,skewY:0,z:0,x:0,y:0,visibility:'visible',delay:0,overwrite:"all"}));

												endfrm.visibility = "visible";
												endfrm.delay = mdelay;
												endfrm.onComplete = animcompleted();
												endfrm.opacity = 1;
												endfrm.force3D="auto";
												if (ncc.match("randomrotate") && animobject != nextcaption) {

													for (var i=0;i<animobject.length;i++) {
														var obj =new Object();
														var endobj = new Object();
														jQuery.extend(obj,frm);
														jQuery.extend(endobj,endfrm);
														frm.scale = Math.random()*3+1;
														frm.rotation = Math.round(Math.random()*200-100);
														frm.x = Math.round(Math.random()*200-100);
														frm.y = Math.round(Math.random()*200-100);

														if (i!=0) endobj.delay = mdelay + (i*elemdelay);


														tl.append(punchgs.TweenLite.fromTo(animobject[i],mspeed,obj,endobj),"frame0");
													}



												}	else
												tl.add(newtl.staggerFromTo(animobject,mspeed,frm,endfrm,elemdelay),"frame0");
												//tl.add(punchgs.TweenLite.fromTo(nextcaption,mspeed,frm,endfrm),"frame0");
										}
									}

									// SAVE IT TO NCAPTION BEFORE NEW STEPS WILL BE ADDED
									nextcaption.data('timeline',tl);

									// FURTHER ANIMATIONS IN CASE THERE ARE MORE THAN ONE STEP IN THE ANIMATION CHAIN
									var frames = new Array();
									if (nextcaption.data('frames')!=undefined) {
										var rowtext = nextcaption.data('frames');
										rowtext = rowtext.replace(/\s+/g, '');
										rowtext = rowtext.replace("{","");
										var spframes = rowtext.split('}');
										jQuery.each(spframes,function(index,spframe){
											if (spframe.length>0) {
												var params = getAnimSteps(spframe);

												addMoveCaption(nextcaption,opt,params,"frame"+(index+10),xbw)

											}
										})
									} // END OF ANIMATION STEPS

									tl = nextcaption.data('timeline');
									// IF THERE IS ANY EXIT ANIM DEFINED
									// For Static Layers -> 1 -> In,  2-> Out  0-> Ignore  -1-> Not Static
									if ((nextcaption.data('end')!=undefined) && (staticdirection==-1 || staticdirection==2)) {
										endMoveCaption(nextcaption,opt,nextcaption.data('end')/1000,frm,"frame99",xbw);
									} else {
										if (staticdirection==-1 || staticdirection==2)
											endMoveCaption(nextcaption,opt,999999,frm,"frame99",xbw);
										else
											endMoveCaption(nextcaption,opt,200,frm,"frame99",xbw);
									}

									// SAVE THE TIMELINE IN DOM ELEMENT
									tl = nextcaption.data('timeline');
									nextcaption.data('timeline',tl);
									callCaptionLoops(nextcaption,xbw);
									tl.resume();
							 }
						  }

						  if (internrecalled) {
						  			killCaptionLoops(nextcaption);
						  			callCaptionLoops(nextcaption,xbw);

							  		if (nextcaption.data('timeline') != undefined) {
								  		var tweens = nextcaption.data('timeline').getTweensOf();
								  		jQuery.each(tweens,function(index,tween) {
									  		if (tween.vars.data != undefined) {
									  			var newx =  tween.vars.data.oldx * xbw;
									  			var newy =  tween.vars.data.oldy * xbw;
									  			if (tween.progress() !=1 && tween.progress()!=0) {
									  				try{
											  			//tween.updateTo({x:newx, y:newy},true);
											  			tween.vars.x = newx;
											  			tween.vary.y = newy;
											  		  } catch(e) {

											  		  }
										  		} else {
										  			if (tween.progress()==1) {
											  				punchgs.TweenLite.set(tween.target,{x:newx,y:newy});
											  		}
											  	}
									  		}
								  		})
								  	}
						  }

					})

						var bt=jQuery('body').find('#'+opt.container.attr('id')).find('.tp-bannertimer');
						bt.data('opt',opt);



					if (mtl != undefined) setTimeout(function() {
						mtl.resume();
					},30);

				}


				var get_browser = function(){
				    var N=navigator.appName, ua=navigator.userAgent, tem;
				    var M=ua.match(/(opera|chrome|safari|firefox|msie)\/?\s*(\.?\d+(\.\d+)*)/i);
				    if(M && (tem= ua.match(/version\/([\.\d]+)/i))!= null) M[2]= tem[1];
				    M=M? [M[1], M[2]]: [N, navigator.appVersion, '-?'];
				    return M[0];
				    }
				var get_browser_version  = function(){
				    var N=navigator.appName, ua=navigator.userAgent, tem;
				    var M=ua.match(/(opera|chrome|safari|firefox|msie)\/?\s*(\.?\d+(\.\d+)*)/i);
				    if(M && (tem= ua.match(/version\/([\.\d]+)/i))!= null) M[2]= tem[1];
				    M=M? [M[1], M[2]]: [N, navigator.appVersion, '-?'];
				    return M[1];
				    }

				/////////////////////////////////////////////////////////////////
				//	-	CALCULATE THE RESPONSIVE SIZES OF THE CAPTIONS	-	  //
				/////////////////////////////////////////////////////////////////
				var calcCaptionResponsive = function(nc,opt) {
								if (nc.data('fsize') == undefined) nc.data('fsize',parseInt(nc.css('font-size'),0) || 0);
								if (nc.data('pt') == undefined) nc.data('pt',parseInt(nc.css('paddingTop'),0) || 0);
								if (nc.data('pb') == undefined) nc.data('pb',parseInt(nc.css('paddingBottom'),0) || 0);
								if (nc.data('pl') == undefined) nc.data('pl',parseInt(nc.css('paddingLeft'),0) || 0);
								if (nc.data('pr') == undefined) nc.data('pr',parseInt(nc.css('paddingRight'),0) || 0);

								if (nc.data('mt') == undefined) nc.data('mt',parseInt(nc.css('marginTop'),0) || 0);
								if (nc.data('mb') == undefined) nc.data('mb',parseInt(nc.css('marginBottom'),0) || 0);
								if (nc.data('ml') == undefined) nc.data('ml',parseInt(nc.css('marginLeft'),0) || 0);
								if (nc.data('mr') == undefined) nc.data('mr',parseInt(nc.css('marginRight'),0) || 0);

								if (nc.data('bt') == undefined) nc.data('bt',parseInt(nc.css('borderTopWidth'),0) || 0);
								if (nc.data('bb') == undefined) nc.data('bb',parseInt(nc.css('borderBottomWidth'),0) || 0);
								if (nc.data('bl') == undefined) nc.data('bl',parseInt(nc.css('borderLeftWidth'),0) || 0);
								if (nc.data('br') == undefined) nc.data('br',parseInt(nc.css('borderRightWidth'),0) || 0);

								if (nc.data('ls') == undefined) nc.data('ls',parseInt(nc.css('letterSpacing'),0) || 0);

								if (nc.data('lh') == undefined) nc.data('lh',parseInt(nc.css('lineHeight'),0) || "auto");
								if (nc.data('minwidth') == undefined) nc.data('minwidth',parseInt(nc.css('minWidth'),0) || 0);
								if (nc.data('minheight') == undefined) nc.data('minheight',parseInt(nc.css('minHeight'),0) || 0);
								if (nc.data('maxwidth') == undefined) nc.data('maxwidth',parseInt(nc.css('maxWidth'),0) || "none");
								if (nc.data('maxheight') == undefined) nc.data('maxheight',parseInt(nc.css('maxHeight'),0) || "none");
								if (nc.data('wii') == undefined) nc.data('wii',parseInt(nc.css('width'),0) || 0);
								if (nc.data('hii') == undefined) nc.data('hii',parseInt(nc.css('height'),0) || 0);

								if (nc.data('wan') == undefined) nc.data('wan',nc.css("-webkit-transition"));
								if (nc.data('moan') == undefined) nc.data('moan',nc.css("-moz-animation-transition"));
								if (nc.data('man') == undefined) nc.data('man',nc.css("-ms-animation-transition"));
								if (nc.data('ani') == undefined) nc.data('ani',nc.css("transition"));

								// IE8 FIX FOR AUTO LINEHEIGHT
								if (nc.data('lh')=="auto") nc.data('lh',nc.data('fsize')+4);




								if (!nc.hasClass("tp-splitted")) {


										nc.css("-webkit-transition", "none");
									    nc.css("-moz-transition", "none");
									    nc.css("-ms-transition", "none");
									    nc.css("transition", "none");

										punchgs.TweenLite.set(nc,{
														 fontSize: Math.round((nc.data('fsize') * opt.bw))+"px",

														 letterSpacing:Math.floor((nc.data('ls') * opt.bw))+"px",

														 paddingTop: Math.round((nc.data('pt') * opt.bh)) + "px",
														 paddingBottom: Math.round((nc.data('pb') * opt.bh)) + "px",
														 paddingLeft: Math.round((nc.data('pl') * opt.bw)) + "px",
														 paddingRight: Math.round((nc.data('pr') * opt.bw)) + "px",

														 marginTop: (nc.data('mt') * opt.bh) + "px",
														 marginBottom: (nc.data('mb') * opt.bh) + "px",
														 marginLeft: (nc.data('ml') * opt.bw) + "px",
														 marginRight: (nc.data('mr') * opt.bw) + "px",

														 borderTopWidth: Math.round((nc.data('bt') * opt.bh)) + "px",
														 borderBottomWidth: Math.round((nc.data('bb') * opt.bh)) + "px",
														 borderLeftWidth: Math.round((nc.data('bl') * opt.bw)) + "px",
														 borderRightWidth: Math.round((nc.data('br') * opt.bw)) + "px",

														 lineHeight: Math.round((nc.data('lh') * opt.bh)) + "px",
														 minWidth:(nc.data('minwidth') * opt.bw) + "px",
														 minHeight:(nc.data('minheight') * opt.bh) + "px",

														/* width:(nc.data('wii') * opt.bw) + "px",
														 height:(nc.data('hii') * opt.bh) + "px",														 */

														 overwrite:"auto"
										});
										setTimeout(function() {
											nc.css("-webkit-transition", nc.data('wan'));
										    nc.css("-moz-transition", nc.data('moan'));
										    nc.css("-ms-transition", nc.data('man'));
										    nc.css("transition", nc.data('ani'));

										},30);

										//konsole.log(nc.data('maxwidth')+"  "+nc.data('maxheight'));
										if (nc.data('maxheight')!='none')
											nc.css({'maxHeight':(nc.data('maxheight') * opt.bh) + "px"});


										if (nc.data('maxwidth')!='none')
											nc.css({'maxWidth':(nc.data('maxwidth') * opt.bw) + "px"});
								}
						}


				/******************************
					-	CAPTION LOOPS	-
				********************************/


				var callCaptionLoops = function(nextcaption,factor) {

									// SOME LOOPING ANIMATION ON INTERNAL ELEMENTS
									nextcaption.find('.rs-pendulum').each(function() {
										var el = jQuery(this);
										if (el.data('timeline')==undefined) {
											el.data('timeline',new punchgs.TimelineLite);
											var startdeg = el.data('startdeg')==undefined ? -20 : el.data('startdeg'),
												enddeg = el.data('enddeg')==undefined ? 20 : el.data('enddeg'),
												speed = el.data('speed')==undefined ? 2 : el.data('speed'),
												origin = el.data('origin')==undefined ? "50% 50%" : el.data('origin'),
												easing = el.data('easing')==undefined ? punchgs.Power2.easeInOut : el.data('ease');

											startdeg = startdeg * factor;
											enddeg = enddeg * factor;

											el.data('timeline').append(new punchgs.TweenLite.fromTo(el,speed,{force3D:"auto",rotation:startdeg,transformOrigin:origin},{rotation:enddeg,ease:easing}));
											el.data('timeline').append(new punchgs.TweenLite.fromTo(el,speed,{force3D:"auto",rotation:enddeg,transformOrigin:origin},{rotation:startdeg,ease:easing,onComplete:function() {
												el.data('timeline').restart();
											}}));
										}

									})

									// SOME LOOPING ANIMATION ON INTERNAL ELEMENTS
									nextcaption.find('.rs-rotate').each(function() {
										var el = jQuery(this);
										if (el.data('timeline')==undefined) {
											el.data('timeline',new punchgs.TimelineLite);
											var startdeg = el.data('startdeg')==undefined ? 0 : el.data('startdeg'),
												enddeg = el.data('enddeg')==undefined ? 360 : el.data('enddeg');
												speed = el.data('speed')==undefined ? 2 : el.data('speed'),
												origin = el.data('origin')==undefined ? "50% 50%" : el.data('origin'),
												easing = el.data('easing')==undefined ? punchgs.Power2.easeInOut : el.data('easing');

											startdeg = startdeg * factor;
											enddeg = enddeg * factor;

											el.data('timeline').append(new punchgs.TweenLite.fromTo(el,speed,{force3D:"auto",rotation:startdeg,transformOrigin:origin},{rotation:enddeg,ease:easing,onComplete:function() {
												el.data('timeline').restart();
											}}));
										}

									})

									// SOME LOOPING ANIMATION ON INTERNAL ELEMENTS
									nextcaption.find('.rs-slideloop').each(function() {
										var el = jQuery(this);
										if (el.data('timeline')==undefined) {
											el.data('timeline',new punchgs.TimelineLite);
											var xs = el.data('xs')==undefined ? 0 : el.data('xs'),
												ys = el.data('ys')==undefined ? 0 : el.data('ys'),
												xe = el.data('xe')==undefined ? 0 : el.data('xe'),
												ye = el.data('ye')==undefined ? 0 : el.data('ye'),
												speed = el.data('speed')==undefined ? 2 : el.data('speed'),
												easing = el.data('easing')==undefined ? punchgs.Power2.easeInOut : el.data('easing');

												xs = xs * factor;
												ys = ys * factor;
												xe = xe * factor;
												ye = ye * factor;

											el.data('timeline').append(new punchgs.TweenLite.fromTo(el,speed,{force3D:"auto",x:xs,y:ys},{x:xe,y:ye,ease:easing}));
											el.data('timeline').append(new punchgs.TweenLite.fromTo(el,speed,{force3D:"auto",x:xe,y:ye},{x:xs,y:ys,onComplete:function() {
												el.data('timeline').restart();
											}}));
										}

									})

									// SOME LOOPING ANIMATION ON INTERNAL ELEMENTS
									nextcaption.find('.rs-pulse').each(function() {
										var el = jQuery(this);
										if (el.data('timeline')==undefined) {
											el.data('timeline',new punchgs.TimelineLite);
											var zoomstart = el.data('zoomstart')==undefined ? 0 : el.data('zoomstart'),
												zoomend = el.data('zoomend')==undefined ? 0 : el.data('zoomend'),
												speed = el.data('speed')==undefined ? 2 : el.data('speed'),
												easing = el.data('easing')==undefined ? punchgs.Power2.easeInOut : el.data('easing');

											el.data('timeline').append(new punchgs.TweenLite.fromTo(el,speed,{force3D:"auto",scale:zoomstart},{scale:zoomend,ease:easing}));
											el.data('timeline').append(new punchgs.TweenLite.fromTo(el,speed,{force3D:"auto",scale:zoomend},{scale:zoomstart,onComplete:function() {
												el.data('timeline').restart();
											}}));
										}

									})

									nextcaption.find('.rs-wave').each(function() {
										var el = jQuery(this);
										if (el.data('timeline')==undefined) {
											el.data('timeline',new punchgs.TimelineLite);

											var angle= el.data('angle')==undefined ? 10 : el.data('angle'),
												radius = el.data('radius')==undefined ? 10 : el.data('radius'),
												speed = el.data('speed')==undefined ? -20 : el.data('speed'),
												origin = el.data('origin')==undefined ? -20 : el.data('origin');

												angle = angle*factor;
												radius = radius * factor;

											var angobj = {a:0, ang : angle, element:el, unit:radius};


												el.data('timeline').append(new punchgs.TweenLite.fromTo(angobj,speed,
																			{	a:360	},
																			{	a:0,
																				force3D:"auto",
																				ease:punchgs.Linear.easeNone,
																				onUpdate:function() {

																					var rad = angobj.a * (Math.PI / 180);
																		            punchgs.TweenLite.to(angobj.element,0.1,{force3D:"auto",x:Math.cos(rad) * angobj.unit, y:angobj.unit * (1 - Math.sin(rad))});

																				},
																				onComplete:function() {
																					el.data('timeline').restart();
																				}
																			}
																			));
										}

									})
				}

				var killCaptionLoops = function(nextcaption) {
							// SOME LOOPING ANIMATION ON INTERNAL ELEMENTS
							nextcaption.find('.rs-pendulum, .rs-slideloop, .rs-pulse, .rs-wave').each(function() {
								var el = jQuery(this);
								if (el.data('timeline')!=undefined) {
										el.data('timeline').pause();
										el.data('timeline',null);
									}
								});
				}

				//////////////////////////
				//	REMOVE THE CAPTIONS //
				/////////////////////////
				var removeTheCaptions = function(actli,opt) {

						var removetime = 0;

						var allcaptions = actli.find('.tp-caption'),
							allstaticcaptions = opt.container.find('.tp-static-layers').find('.tp-caption');


						jQuery.each(allstaticcaptions, function(index,staticcapt) {
							allcaptions.push(staticcapt);
						});

						allcaptions.each(function(i) {



							    var staticdirection = -1;	// 1 -> In,  2-> Out  0-> Ignore  -1-> Not Static

								var nextcaption=jQuery(this);
								if (nextcaption.hasClass("tp-static-layer")) {

									if (nextcaption.data('startslide') == -1 || nextcaption.data('startslide') == "-1")
										nextcaption.data('startslide',0);

									if (nextcaption.data('endslide') == -1 || nextcaption.data('endslide') == "-1")
										nextcaption.data('endslide',opt.slideamount);



									// IF STATIC ITEM CURRENTLY NOT VISIBLE
									if (nextcaption.hasClass("tp-is-shown")) {

										if ((nextcaption.data('startslide') > opt.next) ||
											(nextcaption.data('endslide') < opt.next)) {

											staticdirection = 2;
											nextcaption.removeClass("tp-is-shown");
										} else {
											staticdirection = 0;
										}
									} else {
										staticdirection = 2;
									}



								}



							if (staticdirection != 0 ) {

									killCaptionLoops(nextcaption);

									if (nextcaption.find('iframe').length>0) {
																	// VIMEO VIDEO PAUSE
																	//if (nextcaption.data('vimeoid')!=undefined && String(nextcaption.data('vimeoid')).length>0)
																	  	punchgs.TweenLite.to(nextcaption.find('iframe'),0.2,{autoAlpha:0});
																	  	if (is_mobile()) nextcaption.find('iframe').remove();
																	try {
																		var ifr = nextcaption.find('iframe');
																		var id = ifr.attr('id');
																		var froogaloop = $f(id);
																		froogaloop.api("pause");
																		clearTimeout(nextcaption.data('timerplay'));
																	} catch(e) {}

																	try {
																		var player=nextcaption.data('player');
																		player.stopVideo();
																		clearTimeout(nextcaption.data('timerplay'));
																	} catch(e) {}
																}

									// IF HTML5 VIDEO IS EMBEDED
									if (nextcaption.find('video').length>0) {
													try{
														nextcaption.find('video').each(function(i) {
															var html5vid = jQuery(this).parent();
															var videoID =html5vid.attr('id');
															clearTimeout(html5vid.data('timerplay'));
															var video = this;
															video.pause();
														})
													}catch(e) {}
												} // END OF VIDEO JS FUNCTIONS
									try {

											//var tl = punchgs.TimelineLite.exportRoot();
											var tl = nextcaption.data('timeline');
											var endstarts = tl.getLabelTime("frame99");
											var curtime = tl.time();
											if (endstarts>curtime) {

												// WE NEED TO STOP ALL OTHER NIMATIONS
												var tweens = tl.getTweensOf(nextcaption);
												jQuery.each(tweens,function(index,tw) {

													if (index!=0)
														tw.pause();
												});
												if (nextcaption.css('opacity')!=0) {
													var spp = nextcaption.data('endspeed') == undefined ? nextcaption.data('speed') : nextcaption.data('endspeed');
													if (spp>removetime) removetime =spp;
													tl.play("frame99");
												} else
													tl.progress(1,false);
											}

										} catch(e) {}

							}

						});

						return removetime;
				}

				//////////////////////////////
				//	MOVE THE CAPTIONS  //
				////////////////////////////
				var addMoveCaption = function(nextcaption,opt,params,frame,downscale) {
							var tl = nextcaption.data('timeline');

							var newtl = new punchgs.TimelineLite();

							var animobject = nextcaption;

							if (params.typ == "chars") animobject = nextcaption.data('mySplitText').chars;
							else
							if (params.typ == "words") animobject = nextcaption.data('mySplitText').words;
							else
							if (params.typ == "lines") animobject = nextcaption.data('mySplitText').lines;
							params.animation.ease = params.ease;

							if (params.animation.rotationZ !=undefined) params.animation.rotation = params.animation.rotationZ;
							params.animation.data = new Object();
							params.animation.data.oldx = params.animation.x;
							params.animation.data.oldy = params.animation.y;

							params.animation.x = params.animation.x * downscale;
							params.animation.y = params.animation.y * downscale;


							tl.add(newtl.staggerTo(animobject,params.speed,params.animation,params.elementdelay),params.start);
							tl.addLabel(frame,params.start);

							nextcaption.data('timeline',tl);

				}
				//////////////////////////////
				//	MOVE OUT THE CAPTIONS  //
				////////////////////////////
				var endMoveCaption = function(nextcaption,opt,mdelay,backwards,frame,downscale) {

									var tl = nextcaption.data('timeline'),
										newtl = new punchgs.TimelineLite();

									var frm = newAnimObject(),
										mspeed= (nextcaption.data('endspeed') == undefined) ? nextcaption.data('speed') : nextcaption.data('endspeed'),
										ncc = nextcaption.attr('class');

									frm.ease = (nextcaption.data('endeasing') == undefined) ? punchgs.Power1.easeInOut : nextcaption.data('endeasing');

									mspeed = mspeed/1000;



									if (ncc.match('ltr') ||
										ncc.match('ltl') ||
										ncc.match('str') ||
										ncc.match('stl') ||
										ncc.match('ltt') ||
										ncc.match('ltb') ||
										ncc.match('stt') ||
										ncc.match('stb') ||
										ncc.match('skewtoright') ||
										ncc.match('skewtorightshort') ||
										ncc.match('skewtoleft') ||
										ncc.match('skewtoleftshort') ||
										ncc.match('fadeout') ||
										ncc.match("randomrotateout"))
									{

										if (ncc.match('skewtoright') || ncc.match('skewtorightshort')) frm.skewX = 35
										else
										if (ncc.match('skewtoleft') || ncc.match('skewtoleftshort')) frm.skewX =  -35


										if (ncc.match('ltr') || ncc.match('skewtoright'))
											frm.x=opt.width+60;
										else if (ncc.match('ltl') || ncc.match('skewtoleft'))
											frm.x=0-(opt.width+60);
										else if (ncc.match('ltt'))
											frm.y=0-(opt.height+60);
										else if (ncc.match('ltb'))
											frm.y=opt.height+60;
										else if (ncc.match('str') || ncc.match('skewtorightshort')) {
											frm.x=50;frm.opacity=0;
										} else if (ncc.match('stl') || ncc.match('skewtoleftshort')) {
											frm.x=-50;frm.opacity=0;
										} else if (ncc.match('stt')) {
											frm.y=-50;frm.opacity=0;
										} else if (ncc.match('stb')) {
											frm.y=50;frm.opacity=0;
										} else if (ncc.match("randomrotateout")) {
											frm.x = Math.random()*opt.width;
											frm.y = Math.random()*opt.height;
											frm.scale = Math.random()*2+0.3;
											frm.rotation = Math.random()*360-180;
											frm.opacity = 0;
										} else if (ncc.match('fadeout')) {
											frm.opacity = 0;
										}

										if (ncc.match('skewtorightshort')) frm.x = 270;
										else
										if (ncc.match('skewtoleftshort')) frm.x =  -270
										frm.data = new Object();
										frm.data.oldx = frm.x;
										frm.data.oldy = frm.y;
										frm.x = frm.x * downscale;
										frm.y = frm.y * downscale;

										frm.overwrite="auto";
										var animobject = nextcaption;
										var animobject = nextcaption;
										if (nextcaption.data('splitout') == "chars") animobject = nextcaption.data('mySplitText').chars;
										else
										if (nextcaption.data('splitout') == "words") animobject = nextcaption.data('mySplitText').words;
										else
										if (nextcaption.data('splitout') == "lines") animobject = nextcaption.data('mySplitText').lines;
										var elemdelay = (nextcaption.data('endelementdelay') == undefined) ? 0 : nextcaption.data('endelementdelay');
										//tl.add(punchgs.TweenLite.to(nextcaption,mspeed,frm),mdelay);
										tl.add(newtl.staggerTo(animobject,mspeed,frm,elemdelay),mdelay);

									}

									else

									if (nextcaption.hasClass("customout")) {

										frm = getAnimDatas(frm,nextcaption.data('customout'));
										var animobject = nextcaption;
										if (nextcaption.data('splitout') == "chars") animobject = nextcaption.data('mySplitText').chars;
										else
										if (nextcaption.data('splitout') == "words") animobject = nextcaption.data('mySplitText').words;
										else
										if (nextcaption.data('splitout') == "lines") animobject = nextcaption.data('mySplitText').lines;

										var elemdelay = (nextcaption.data('endelementdelay') == undefined) ? 0 : nextcaption.data('endelementdelay');
										frm.onStart = function() {

																 punchgs.TweenLite.set(nextcaption,{
																	  transformPerspective:frm.transformPerspective,
																	  transformOrigin:frm.transformOrigin,
																	  overwrite:"auto"
																  });
										}

										frm.data = new Object();
										frm.data.oldx = frm.x;
										frm.data.oldy = frm.y;

										frm.x = frm.x * downscale;
										frm.y = frm.y * downscale;

										tl.add(newtl.staggerTo(animobject,mspeed,frm,elemdelay),mdelay);
									}

									else {
										backwards.delay = 0;
										tl.add(punchgs.TweenLite.to(nextcaption,mspeed,backwards),mdelay);
									}


								tl.addLabel(frame,mdelay);

								nextcaption.data('timeline',tl);
			}

		///////////////////////////
		//	REMOVE THE LISTENERS //
		///////////////////////////
		var removeAllListeners = function(container,opt) {
			container.children().each(function() {
			  try{ jQuery(this).die('click'); } catch(e) {}
			  try{ jQuery(this).die('mouseenter');} catch(e) {}
			  try{ jQuery(this).die('mouseleave');} catch(e) {}
			  try{ jQuery(this).unbind('hover');} catch(e) {}
			})
			try{ container.die('click','mouseenter','mouseleave');} catch(e) {}
			clearInterval(opt.cdint);
			container=null;
		}

		///////////////////////////
		//	-	countDown	-	//
		/////////////////////////
		var countDown = function(container,opt) {
			opt.cd=0;
			opt.loop=0;
			if (opt.stopAfterLoops!=undefined && opt.stopAfterLoops>-1)
					opt.looptogo=opt.stopAfterLoops;
			else
				opt.looptogo=9999999;

			if (opt.stopAtSlide!=undefined && opt.stopAtSlide>-1)
					opt.lastslidetoshow=opt.stopAtSlide;
			else
					opt.lastslidetoshow=999;

			opt.stopLoop="off";

			if (opt.looptogo==0) opt.stopLoop="on";


			if (opt.slideamount >1 && !(opt.stopAfterLoops==0 && opt.stopAtSlide==1) ) {
					var bt=container.find('.tp-bannertimer');


					// LISTENERS  //container.trigger('stoptimer');
					container.on('stoptimer',function() {
						var bt = jQuery(this).find('.tp-bannertimer');
						bt.data('tween').pause();
						if (opt.hideTimerBar=="on") bt.css({visibility:"hidden"});
					});
					container.on('starttimer',function() {

						if (opt.conthover!=1 && opt.videoplaying!=true && opt.width>opt.hideSliderAtLimit && opt.bannertimeronpause != true && opt.overnav !=true)
							if ((opt.stopLoop=="on" && opt.next==opt.lastslidetoshow-1) || opt.noloopanymore == 1)
							   opt.noloopanymore = 1;
							else {

								bt.css({visibility:"visible"});
								bt.data('tween').resume();
							}

							if (opt.hideTimerBar=="on") bt.css({visibility:"hidden"});
					});
					container.on('restarttimer',function() {
						var bt = jQuery(this).find('.tp-bannertimer');
						if ((opt.stopLoop=="on" && opt.next==opt.lastslidetoshow-1) || opt.noloopanymore == 1)
							   	opt.noloopanymore = 1;
							else {

								bt.css({visibility:"visible"});
								bt.data('tween').kill();
								bt.data('tween',punchgs.TweenLite.fromTo(bt,opt.delay/1000,{width:"0%"},{force3D:"auto",width:"100%",ease:punchgs.Linear.easeNone,onComplete:countDownNext,delay:1}));

							}
							if (opt.hideTimerBar=="on") bt.css({visibility:"hidden"});
					});

					container.on('nulltimer',function() {
							bt.data('tween').pause(0);
							if (opt.hideTimerBar=="on") bt.css({visibility:"hidden"});
					});



					 var countDownNext = function() {
						if (jQuery('body').find(container).length==0) {
							removeAllListeners(container,opt);
							clearInterval(opt.cdint);
						}

						container.trigger("revolution.slide.slideatend");

						//STATE OF API CHANGED -> MOVE TO AIP BETTER
						if (container.data('conthover-changed') == 1) {
							opt.conthover=	container.data('conthover');
							container.data('conthover-changed',0);
						}

						// SWAP TO NEXT BANNER
						opt.act=opt.next;
						opt.next=opt.next+1;

						if (opt.next>container.find('>ul >li').length-1) {
								opt.next=0;
								opt.looptogo=opt.looptogo-1;

								if (opt.looptogo<=0) {
										opt.stopLoop="on";

								}
							}

						// STOP TIMER IF NO LOOP NO MORE NEEDED.

						if (opt.stopLoop=="on" && opt.next==opt.lastslidetoshow-1) {
								container.find('.tp-bannertimer').css({'visibility':'hidden'});
								container.trigger('revolution.slide.onstop');
								opt.noloopanymore = 1;
						} else {
							bt.data('tween').restart();
						}

						// SWAP THE SLIDES
						swapSlide(container,opt);

					}

					bt.data('tween',punchgs.TweenLite.fromTo(bt,opt.delay/1000,{width:"0%"},{force3D:"auto",width:"100%",ease:punchgs.Linear.easeNone,onComplete:countDownNext,delay:1}));
					bt.data('opt',opt);


					container.hover(
						function() {

							if (opt.onHoverStop=="on" && (!is_mobile())) {
								container.trigger('stoptimer');

								container.trigger('revolution.slide.onpause');
								var nextsh = container.find('>ul >li:eq('+opt.next+') .slotholder');
								nextsh.find('.defaultimg').each(function() {
									var dimg = jQuery(this);
									if (dimg.data('kenburn')!=undefined) {
									   dimg.data('kenburn').pause();
									 }
								});
							}
						},
						function() {
							if (container.data('conthover')!=1) {
								container.trigger('revolution.slide.onresume');
								container.trigger('starttimer');

								var nextsh = container.find('>ul >li:eq('+opt.next+') .slotholder');
								nextsh.find('.defaultimg').each(function() {
									var dimg = jQuery(this);
									if (dimg.data('kenburn')!=undefined) {
									   dimg.data('kenburn').play();
									 }
								});
							}
						});
			}
		}


	//////////////////
	// IS MOBILE ?? //
	//////////////////
	var is_mobile = function() {
	    var agents = ['android', 'webos', 'iphone', 'ipad', 'blackberry','Android', 'webos', ,'iPod', 'iPhone', 'iPad', 'Blackberry', 'BlackBerry'];
		var ismobile=false;
	    for(var i in agents) {

		    if (navigator.userAgent.split(agents[i]).length>1) {
	            ismobile = true;

	          }
	    }
	    return ismobile;
	}



/**************************************************************************
 * Revolution Slider - PAN ZOOM MODULE
 * @version: 1.0 (03.06.2013)
 * @author ThemePunch
**************************************************************************/

	/***********************************************
		-	KEN BURN BACKGROUND FIT CALCULATOR	-
	***********************************************/
	var calculateKenBurnScales = function(proc,sloth,opt) {
				var ow = sloth.data('owidth');
				var oh = sloth.data('oheight');

				if (ow / oh > opt.width / opt.height) {
					var factor = (opt.container.width() /ow);
					var nheight = oh * factor;
					var hfactor = (nheight / opt.container.height())*proc;
					proc = proc * (100/hfactor);
					hfactor = 100;
					proc = proc;
					return (proc+"% "+hfactor+"%"+" 1");
				} else {
					var factor = (opt.container.width() /ow);
					var nheight = oh * factor;
					var hfactor = (nheight / opt.container.height())*proc;
					return (proc+"% "+hfactor+"%");
				}
			}



	/******************************
		-	startKenBurn	-
	********************************/
	var startKenBurn = function(container,opt,recalc,prepareonly) {

		try{
			var actli = container.find('>ul:first-child >li:eq('+opt.act+')');
		} catch(e) {
			var actli=container.find('>ul:first-child >li:eq(1)');
		}

		opt.lastslide=opt.act;


		var nextli = container.find('>ul:first-child >li:eq('+opt.next+')'),
			nextsh = nextli.find('.slotholder'),
			bgps = nextsh.data('bgposition'),
			bgpe = nextsh.data('bgpositionend'),
			zos = nextsh.data('zoomstart')/100,
			zoe = nextsh.data('zoomend')/100,
			ros = nextsh.data('rotationstart'),
			roe = nextsh.data('rotationend'),
			bgfs = nextsh.data('bgfit'),
			bgfe = nextsh.data('bgfitend'),
			easeme = nextsh.data('easeme'),
			dur = nextsh.data('duration')/1000,
			bgfb = 100;


			if (bgfs==undefined) bgfs=100;
			if (bgfe==undefined) bgfe=100;
			var obgfs = bgfs,
				obgfe = bgfe;

			bgfs = calculateKenBurnScales(bgfs,nextsh,opt);
			bgfe = calculateKenBurnScales(bgfe,nextsh,opt);
			bgfb = calculateKenBurnScales(100,nextsh,opt);


			if (zos==undefined) zos=1;
			if (zoe==undefined) zoe=1;
			if (ros==undefined) ros=0;
			if (roe==undefined) roe=0;

			if (zos<1) zos=1;
			if (zoe<1) zoe=1;


			var imgobj = new Object();
			imgobj.w = parseInt(bgfb.split(" ")[0],0),
			imgobj.h = parseInt(bgfb.split(" ")[1],0);

			var turned = false;
			if (bgfb.split(" ")[2] == "1") {
				turned = true;
			}

			nextsh.find('.defaultimg').each(function() {
				var defimg = jQuery(this);
				if (nextsh.find('.kenburnimg').length==0)
					nextsh.append('<div class="kenburnimg" style="position:absolute;z-index:1;width:100%;height:100%;top:0px;left:0px;"><img src="'+defimg.attr('src')+'" style="-webkit-touch-callout: none;-webkit-user-select: none;-khtml-user-select: none;-moz-user-select: none;-ms-user-select: none;user-select: none;position:absolute;width:'+imgobj.w+'%;height:'+imgobj.h+'%;"></div>');
				else {
					nextsh.find('.kenburnimg img').css({width:imgobj.w+'%',height:imgobj.h+'%'});
				}



				var kbimg = nextsh.find('.kenburnimg img');


				var imgs = calculateKenBurnImgPos(opt,bgps,bgfs,kbimg,turned),
					imge = calculateKenBurnImgPos(opt,bgpe,bgfe,kbimg,turned);

				if (turned) {
					imgs.w = obgfs/100;
					imge.w = obgfe/100;
				}



				if (prepareonly) {

					punchgs.TweenLite.set(kbimg,{autoAlpha:0,
											transformPerspective:1200,
											transformOrigin:"0% 0%",
											top:0,left:0,
											scale:imgs.w,
											x:imgs.x,
											y:imgs.y});
					var sx = imgs.w,
						ww = (sx * kbimg.width()) - opt.width,
						hh = (sx * kbimg.height()) - opt.height,
						hor = Math.abs((imgs.x / ww)*100),
						ver = Math.abs((imgs.y / hh)*100);
						if (hh==0) ver =0;
						if (ww == 0) hor = 0;
					defimg.data('bgposition',hor+"% "+ver+"%");
					if (!isIE(8)) defimg.data('currotate',getRotationDegrees(kbimg));
					if (!isIE(8)) defimg.data('curscale',(imgobj.w*sx)+"%  "+(imgobj.h*sx+"%"));

					nextsh.find('.kenburnimg').remove();
				}
				else
					defimg.data('kenburn',punchgs.TweenLite.fromTo(kbimg,dur,{autoAlpha:1, force3D:punchgs.force3d, transformOrigin:"0% 0%", top:0,left:0, scale:imgs.w, x:imgs.x, y:imgs.y},{autoAlpha:1,rotationZ:roe,ease:easeme, x:imge.x, y:imge.y,scale:imge.w,onUpdate:function() {
							var sx = kbimg[0]._gsTransform.scaleX;
							var ww = (sx * kbimg.width()) - opt.width,
								hh = (sx * kbimg.height()) - opt.height,
								hor = Math.abs((kbimg[0]._gsTransform.x / ww)*100),
								ver = Math.abs((kbimg[0]._gsTransform.y / hh)*100);
								if (hh==0) ver =0;
								if (ww == 0) hor = 0;

							defimg.data('bgposition',hor+"% "+ver+"%");

							if (!isIE(8)) defimg.data('currotate',getRotationDegrees(kbimg));
							if (!isIE(8)) defimg.data('curscale',(imgobj.w*sx)+"%  "+(imgobj.h*sx+"%"));
							//punchgs.TweenLite.set(defimg,{rotation:defimg.data('currotate'), backgroundPosition:defimg.data('bgposition'), backgroundSize:defimg.data('curscale')});
					}}));
		})
	}

	/*************************************************
		-	CALCULATE KENBURNS IMAGE POSITIONS	-
	**************************************************/

	var calculateKenBurnImgPos = function(opt,bgp,bgf,img,turned) {
			var imgobj = new Object;

			if (!turned)
				imgobj.w = parseInt(bgf.split(" ")[0],0) / 100;
			else
				imgobj.w = parseInt(bgf.split(" ")[1],0) / 100;

			switch(bgp) {
							case "left top":
							case "top left":
								imgobj.x = 0;
								imgobj.y = 0;
							break;
							case "center top":
							case "top center":
								imgobj.x = (((0-img.width()) * imgobj.w) + parseInt(opt.width,0))/2;
								imgobj.y = 0;
							break;
							case "top right":
							case "right top":
								imgobj.x = ((0-img.width()) * imgobj.w) + parseInt(opt.width,0);
								imgobj.y = 0;

							break;
							case "center left":
							case "left center":
								imgobj.x = 0;
								imgobj.y = (((0-img.height()) * imgobj.w) + parseInt(opt.height,0)) / 2;
							break;
							case "center center":
								imgobj.x = (((0-img.width()) * imgobj.w) + parseInt(opt.width,0))/2;
								imgobj.y = (((0-img.height()) * imgobj.w) + parseInt(opt.height,0)) / 2;

							break;
							case "center right":
							case "right center":
								imgobj.x = ((0-img.width()) * imgobj.w) + parseInt(opt.width,0);
								imgobj.y = (((0-img.height()) * imgobj.w) + parseInt(opt.height,0)) / 2;

							break;
							case "bottom left":
							case "left bottom":
								imgobj.x =0;
								imgobj.y = ((0-img.height()) * imgobj.w) + parseInt(opt.height,0);

							break;
							case "bottom center":
							case "center bottom":
								imgobj.x = (((0-img.width()) * imgobj.w) + parseInt(opt.width,0))/2;
								imgobj.y = ((0-img.height()) * imgobj.w) + parseInt(opt.height,0);
							break;
							case "bottom right":
							case "right bottom":
								imgobj.x = ((0-img.width()) * imgobj.w) + parseInt(opt.width,0);
								imgobj.y = ((0-img.height()) * imgobj.w) + parseInt(opt.height,0);
							break;
						}



			return imgobj;
		}

		/******************************
			-	GET ROTATION DEGREES	-
		********************************/
		var getRotationDegrees = function(obj) {
				    var matrix = obj.css("-webkit-transform") ||
				    obj.css("-moz-transform")    ||
				    obj.css("-ms-transform")     ||
				    obj.css("-o-transform")      ||
				    obj.css("transform");
				    if(matrix !== 'none') {
				        var values = matrix.split('(')[1].split(')')[0].split(',');
				        var a = values[0];
				        var b = values[1];
				        var angle = Math.round(Math.atan2(b, a) * (180/Math.PI));
				    } else { var angle = 0; }
				    return (angle < 0) ? angle +=360 : angle;
				}


		/******************************
			-	STOP KEN BURN	-
		********************************/
		var stopKenBurn = function(container,opt) {

			try{
				var actli = container.find('>ul:first-child >li:eq('+opt.act+')');
			} catch(e) {
				var actli=container.find('>ul:first-child >li:eq(1)');
			}

			opt.lastslide=opt.act;

			var nextli = container.find('>ul:first-child >li:eq('+opt.next+')');


			var actsh = actli.find('.slotholder');
			var nextsh = nextli.find('.slotholder');

			container.find('.defaultimg').each(function() {
				var defimg = jQuery(this);
				punchgs.TweenLite.killTweensOf(defimg,false);
				punchgs.TweenLite.set(defimg,{scale:1,rotationZ:0});
				punchgs.TweenLite.killTweensOf(defimg.data('kenburn img'),false);
				if (defimg.data('kenburn') != undefined) {
					defimg.data('kenburn').pause();
				}
				if (defimg.data('currotate') != undefined && defimg.data('bgposition') !=undefined && defimg.data('curscale') != undefined)
					punchgs.TweenLite.set(defimg,{rotation:defimg.data('currotate'), backgroundPosition:defimg.data('bgposition'), backgroundSize:defimg.data('curscale')});
				if (defimg!= undefined && defimg.data('kenburn img') != undefined && defimg.data('kenburn img').length>0) punchgs.TweenLite.set(defimg.data('kenburn img'),{autoAlpha:0});

			});
		}

//// END OF KENBURNS EXTNESION




/**************************************************************************
 * Revolution Slider - PARALLAX MODULE
 * @version: 1.1 (23.06.2013)
 * @author ThemePunch
**************************************************************************/

		/******************************
			-	PARALLAX EFFECT	-
		********************************/
		var checkForParallax = function(container,opt) {
			if (is_mobile() && opt.parallaxDisableOnMobile=="on") return false;

			container.find('>ul:first-child >li').each(function() {
				var li = jQuery(this);
				for (var i = 1; i<=10;i++)
					li.find('.rs-parallaxlevel-'+i).each(function() {
						var pw = jQuery(this);
						pw.wrap('<div style="position:absolute;top:0px;left:0px;width:100%;height:100%;z-index:'+pw.css('zIndex')+'" class="tp-parallax-container" data-parallaxlevel="'+opt.parallaxLevels[i-1]+'"></div>');
					});
			})



			if (opt.parallax=="mouse" || opt.parallax=="scroll+mouse" || opt.parallax=="mouse+scroll") {

						container.mouseenter(function(event) {
							var currslide = container.find('.current-sr-slide-visible');
									var t = container.offset().top,
										l = container.offset().left,
										ex = (event.pageX-l),
										ey =  (event.pageY-t);
									currslide.data("enterx",ex);
									currslide.data("entery",ey);

						})

						container.on('mousemove.hoverdir, mouseleave.hoverdir',function(event) {
							var currslide = container.find('.current-sr-slide-visible');
							switch (event.type) {

								case "mousemove":

										var	t = container.offset().top,
											l = container.offset().left,
											mh = currslide.data("enterx"),
											mv = currslide.data("entery"),
											diffh = (mh - (event.pageX  - l)),
											diffv = (mv - (event.pageY - t));

										currslide.find(".tp-parallax-container").each(function() {
											var pc = jQuery(this),
												pl = parseInt(pc.data('parallaxlevel'),0)/100,
												offsh =	diffh * pl,
												offsv =	diffv * pl;
											if (opt.parallax=="scroll+mouse" || opt.parallax=="mouse+scroll")
												punchgs.TweenLite.to(pc,0.4,{force3D:"auto",x:offsh,ease:punchgs.Power3.easeOut,overwrite:"all"});
											else
												punchgs.TweenLite.to(pc,0.4,{force3D:"auto",x:offsh,y:offsv,ease:punchgs.Power3.easeOut,overwrite:"all"});
										})

								break;
								case "mouseleave":
										currslide.find(".tp-parallax-container").each(function() {
											var pc = jQuery(this);
											if (opt.parallax=="scroll+mouse" || opt.parallax=="mouse+scroll")
												punchgs.TweenLite.to(pc,1.5,{force3D:"auto",x:0,ease:punchgs.Power3.easeOut});
											else
												punchgs.TweenLite.to(pc,1.5,{force3D:"auto",x:0,y:0,ease:punchgs.Power3.easeOut});
										})
								break;
							}
						});

						if (is_mobile())
							window.ondeviceorientation = function(event) {
							  var 	y = Math.round(event.beta  || 0),
							  		x = Math.round(event.gamma || 0);

							  var currslide = container.find('.current-sr-slide-visible');


							  if (jQuery(window).width() > jQuery(window).height()){
							  		var xx = x;
							  		x = y;
							  		y = xx;

							  }

								var curh = 360/container.width() * x,
							  		curv = 180/container.height() * y;




							  currslide.find(".tp-parallax-container").each(function() {
												var pc = jQuery(this),
													pl = parseInt(pc.data('parallaxlevel'),0)/100,
													offsh =	curh * pl,
													offsv =	curv * pl;
												punchgs.TweenLite.to(pc,0.2,{force3D:"auto",x:offsh,y:offsv,ease:punchgs.Power3.easeOut});
											})

							  // y: -90 -> +90,  x:-180 -> +180

							  //jQuery('.logo-container').html("h:"+curh+"  v:"+curv);
							  }
			}
			if (opt.parallax=="scroll" || opt.parallax=="scroll+mouse" || opt.parallax=="mouse+scroll") {

						jQuery(window).on('scroll',function(event) {
							scrollParallax(container,opt);
						});
			}
		}

		/***************************************
			-	SET POST OF SCROLL PARALLAX	-
		***************************************/
		var scrollParallax = function(container,opt) {
			if (is_mobile() && opt.parallaxDisableOnMobile=="on") return false;
			var t = container.offset().top,
					st = jQuery(window).scrollTop(),
					dist = t+container.height()/2,
					mv = t+container.height()/2 - st,
					wh = jQuery(window).height()/2,
					diffv= wh - mv;

			if (dist<wh) diffv = diffv - (wh-dist);
			var currslide = container.find('.current-sr-slide-visible');
			container.find(".tp-parallax-container").each(function(i) {
				var pc = jQuery(this),
					pl = parseInt(pc.data('parallaxlevel'),0)/100,
					offsv =	diffv * pl;
				pc.data('parallaxoffset',offsv);
				punchgs.TweenLite.to(pc,0.2,{force3D:"auto",y:offsv,ease:punchgs.Power3.easeOut});
			})

			if (opt.parallaxBgFreeze!="on") {
				var pl = opt.parallaxLevels[0]/100,
					offsv =	diffv * pl;
				punchgs.TweenLite.to(container,0.2,{force3D:"auto",y:offsv,ease:punchgs.Power3.easeOut});
			}
		}

		/**************************************************************************
		 * Revolution Slider - THUMBNAIL MODULE
		 * @version: 1.0 (03.06.2013)
		 * @author ThemePunch
		**************************************************************************/


		////////////////////////////////
		//	-	CREATE THE BULLETS -  //
		////////////////////////////////
		var createThumbs = function(container,opt) {

			var cap=container.parent();



			if (opt.navigationType=="thumb" || opt.navsecond=="both") {
						cap.append('<div class="tp-bullets tp-thumbs '+opt.navigationStyle+'"><div class="tp-mask"><div class="tp-thumbcontainer"></div></div></div>');
			}
			var bullets = cap.find('.tp-bullets.tp-thumbs .tp-mask .tp-thumbcontainer');
			var bup = bullets.parent();

			bup.width(opt.thumbWidth*opt.thumbAmount);
			bup.height(opt.thumbHeight);
			bup.parent().width(opt.thumbWidth*opt.thumbAmount);
			bup.parent().height(opt.thumbHeight);

			container.find('>ul:first >li').each(function(i) {
							var li= container.find(">ul:first >li:eq("+i+")");
							var bgcolor = li.find(".defaultimg").css("backgroundColor");
							if (li.data('thumb') !=undefined)
								var src= li.data('thumb')
							else
								var src=li.find("img:first").attr('src');


							bullets.append('<div class="bullet thumb" style="background-color:'+bgcolor+';position:relative;width:'+opt.thumbWidth+'px;height:'+opt.thumbHeight+'px;background-image:url('+src+') !important;background-size:cover;background-position:center center;"></div>');
							var bullet= bullets.find('.bullet:first');
				});
			//bullets.append('<div style="clear:both"></div>');
			var minwidth=10;


			// ADD THE BULLET CLICK FUNCTION HERE
			bullets.find('.bullet').each(function(i) {
				var bul = jQuery(this);

				if (i==opt.slideamount-1) bul.addClass('last');
				if (i==0) bul.addClass('first');
				bul.width(opt.thumbWidth);
				bul.height(opt.thumbHeight);

				if (minwidth<bul.outerWidth(true)) minwidth=bul.outerWidth(true);
				bul.click(function() {
					if (opt.transition==0 && bul.index() != opt.act) {
						opt.next = bul.index();
						callingNewSlide(opt,container);
					}
				});
			});


			var max=minwidth*container.find('>ul:first >li').length;

			var thumbconwidth=bullets.parent().width();
			opt.thumbWidth = minwidth;



			////////////////////////
			// SLIDE TO POSITION  //
			////////////////////////
			if (thumbconwidth<max) {
				jQuery(document).mousemove(function(e) {
					jQuery('body').data('mousex',e.pageX);
				});



				// ON MOUSE MOVE ON THE THUMBNAILS EVERYTHING SHOULD MOVE :)

				bullets.parent().mouseenter(function() {
						var $this=jQuery(this);

						var offset = $this.offset(),
							x = jQuery('body').data('mousex')-offset.left,
							thumbconwidth=$this.width(),
							minwidth=$this.find('.bullet:first').outerWidth(true),
							max=minwidth*container.find('>ul:first >li').length,
							diff=(max- thumbconwidth)+15,
							steps = diff / thumbconwidth;

						$this.addClass("over");
						x=x-30;

						//ANIMATE TO POSITION
						var pos=(0-((x)*steps));
						if (pos>0) pos =0;
						if (pos<0-max+thumbconwidth) pos=0-max+thumbconwidth;
						moveThumbSliderToPosition($this,pos,200);
				});

				bullets.parent().mousemove(function() {

								var $this=jQuery(this),
									offset = $this.offset(),
									x = jQuery('body').data('mousex')-offset.left,
									thumbconwidth=$this.width(),
									minwidth=$this.find('.bullet:first').outerWidth(true),
									max=minwidth*container.find('>ul:first >li').length-1,
									diff=(max- thumbconwidth)+15,
									steps = diff / thumbconwidth;

								x=x-3;
								if (x<6) x=0;
								if (x+3>thumbconwidth-6) x=thumbconwidth;

								//ANIMATE TO POSITION
								var pos=(0-((x)*steps));
								if (pos>0) pos =0;
								if (pos<0-max+thumbconwidth) pos=0-max+thumbconwidth;
								moveThumbSliderToPosition($this,pos,0);

				});

				bullets.parent().mouseleave(function() {
								var $this=jQuery(this);
								$this.removeClass("over");
								moveSelectedThumb(container);
				});
			}


		}


		///////////////////////////////
		//	SelectedThumbInPosition //
		//////////////////////////////
		var moveSelectedThumb = function(container) {

									var bullets=container.parent().find('.tp-bullets.tp-thumbs .tp-mask .tp-thumbcontainer'),
										$this=bullets.parent(),
										offset = $this.offset(),
										minwidth=$this.find('.bullet:first').outerWidth(true),
										x = $this.find('.bullet.selected').index() * minwidth,
										thumbconwidth=$this.width(),
										minwidth=$this.find('.bullet:first').outerWidth(true),
										max=minwidth*container.find('>ul:first >li').length,
										diff=(max- thumbconwidth),
										steps = diff / thumbconwidth,
										pos=0-x;

									if (pos>0) pos =0;
									if (pos<0-max+thumbconwidth) pos=0-max+thumbconwidth;
									if (!$this.hasClass("over")) {
										moveThumbSliderToPosition($this,pos,200);
									}
		}


		////////////////////////////////////
		//	MOVE THUMB SLIDER TO POSITION //
		///////////////////////////////////
		var moveThumbSliderToPosition = function($this,pos,speed) {
			punchgs.TweenLite.to($this.find('.tp-thumbcontainer'),0.2,{force3D:"auto",left:pos,ease:punchgs.Power3.easeOut,overwrite:"auto"});
		}
})(jQuery);



/// END OF THUMBNAIL EXTNESIONS






// SOME ERROR MESSAGES IN CASE THE PLUGIN CAN NOT BE LOADED
function revslider_showDoubleJqueryError(sliderID) {
	var errorMessage = "Revolution Slider Error: You have some jquery.js library include that comes after the revolution files js include.";
	errorMessage += "<br> This includes make eliminates the revolution slider libraries, and make it not work.";
	errorMessage += "<br><br> To fix it you can:<br>&nbsp;&nbsp;&nbsp; 1. In the Slider Settings -> Troubleshooting set option:  <strong><b>Put JS Includes To Body</b></strong> option to true.";
	errorMessage += "<br>&nbsp;&nbsp;&nbsp; 2. Find the double jquery.js include and remove it.";
	errorMessage = "<span style='font-size:16px;color:#BC0C06;'>" + errorMessage + "</span>"
		jQuery(sliderID).show().html(errorMessage);
}


