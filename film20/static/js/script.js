/**
* Filmaster JavaScript scripts
*/

"use strict";
var FM = window.FM || {};

FM.API_VERSION = "1.1";
FM.API_PREFIX = '/api/' + FM.API_VERSION;

FM.fixMarkup = function(scope) {
    var $meter = scope.find("meter");
    if($meter.length > 0 && ((navigator.userAgent.indexOf("Chrome") !== -1) || (navigator.userAgent.indexOf("Opera") !== -1))) {
        for (var i = 0; i < $meter.length; i++) {
            var meter_class = $meter[i].className || "meter",
                meter_value = $meter[i].value
            ;
            if(meter_value) {
                meter_class += " r" + meter_value;
            }
            $($meter[i]).hide().after('<span value="' + meter_value + '" class="' + meter_class + '">' + $meter[i].innerHTML + '</span>')
        }
    }
    FM.showAllScreenings({
        selector: scope.find("#film-cinema-screenings > ul"),
        limit: 3
    });

    FM.filmCheckinButton(scope);
    FM.rateMovieWidget({widget:scope.find('.rate-movie')})

//    FM.ajaxizeSignupForm(scope)
    FM.showAjaxSignup(scope)
    window.fb_init && fb_init(scope);
};

/**
 * Window has focus
 */

FM.hasFocus = false;

function windowBlur() {
    FM.hasFocus = false;
};

function windowFucus() {
    FM.hasFocus = true;
    $( window ).unbind( "mouseenter", windowFucus );
};

$( window ).bind( "mouseenter", windowFucus );
$( window ).bind( "focus"     , windowFucus );
$( window ).bind( "blur"      , windowBlur );


/**
 * dirty markup fixes
 */
(function() {
    var ie7 = $('html').hasClass("ie7"),
        ie8 = $('html').hasClass("ie8")
    ;

    // last child
    if (ie7 || ie8) {
        var $main = $('#main');
        $main.find('ul.not-seen-yet-actions > li:last').addClass('last-child');
        $main.find('div.stream > section > p:last-child').addClass('last-child');
    }
    var $meter = $("meter");
    if($meter.length > 0 && ((navigator.userAgent.indexOf("Chrome") !== -1) || (navigator.userAgent.indexOf("Opera") !== -1))) {
        for (var i = 0; i < $meter.length; i++) {
            var meter_class = $meter[i].className || "meter",
                meter_value = $meter[i].value
            ;
            if(meter_value) {
                meter_class += " r" + meter_value;
            }
            $($meter[i]).hide().after('<span value="' + meter_value + '" class="' + meter_class + '">' + $meter[i].innerHTML + '</span>')
        }
    }
}());

/**
 * carousel
 * @param config
 * @requires UL and LIs positioned relatively
 * TODO:
 * - auto rotate
 * - load images on demand
 * - grey disabled prev/next buttons
 * - DRY, DRY, DRY!!!
 */
FM.carouselGenreMovies = function(config) {
    var $genre_carousel = $(config.genre_carousel),
            $movie_carousel = $(config.movie_carousel),
            $seeall_carousel = $(config.seeall_carousel)
    ;

    // trigger carousel rotation
    function triggerCarousel(direction) {
        if (direction === "next") {
            $next_button.trigger("click");
        } else {
            $prev_button.trigger("click");
        }
    }

    if ($movie_carousel.length && $genre_carousel.length && $seeall_carousel) {
        var $genre_container = $(config.genre_container),
                $movie_container = $(config.movie_container),
                $seeall_container = $(config.seeall_container),
                genre_container_width = 0,
                movie_container_width = 0,
                seeall_container_width = 0,
                genre_carousel_width = 0,
                movie_carousel_width = 0,
                seeall_carousel_width = 0,
                genre_option_width = 0,
                movie_option_width = 0,
                seeall_option_width = 0,
                t,
                direction = "next",
                delay = config.delay,
                $prev_button = $('<a class="prev" title=' + config.prev_msg + ' href="#">' + config.prev_msg + "</a>"),
                $next_button = $('<a class="next" title=' + config.next_msg + ' href="#">' + config.next_msg + "</a>"),
                block_left = true,
                block_right = false
                ;

        // set option width
        if (!movie_option_width) {
            movie_option_width = $movie_container.find("li")[0].offsetWidth;
        }
        if (!genre_option_width) {
            genre_option_width = $genre_container.find("li")[0].offsetWidth;
        }
        if (!seeall_option_width) {
            seeall_option_width = $seeall_container.find("li")[0].offsetWidth;
        }

        // set all options' width
        movie_container_width = movie_option_width * $movie_container.find("li").length;
        genre_container_width = genre_option_width * $genre_container.find("li").length;
        seeall_container_width = seeall_option_width * $seeall_container.find("li").length;

        // set option container width
        $movie_container.css("width", movie_container_width);
        $genre_container.css("width", genre_container_width);
        $seeall_container.css("width", genre_container_width);

        // set carouse width
        movie_carousel_width = $movie_carousel.get(0).offsetWidth;
        genre_carousel_width = $genre_carousel.get(0).offsetWidth;
        seeall_carousel_width = $seeall_carousel.get(0).offsetWidth;

        // visually block prev button
        $prev_button.addClass("blocked");

        // prev button
        $prev_button.bind("click", function() {
            block_right = false;
            $next_button.removeClass("blocked");
            if (!block_left) {
                block_left = true;
                $movie_container.animate({"left": "+=" + movie_option_width * 4}, "slow", function() {
                    // check if the left end is reached
                    block_left = ($movie_container.css("left") === "0px");
                    if (block_left) {
                        $prev_button.addClass("blocked");
                        direction = "next";
                    }
                });
                $genre_container.animate({"left": "+=" + genre_option_width}, "slow");
                $seeall_container.animate({"left": "+=" + genre_option_width}, "slow");
            }
            return false;
        });

        // next button
        $next_button.bind("click", function() {
            block_left = false;
            $prev_button.removeClass("blocked");
            if (!block_right) {
                block_right = true;
                $movie_container.animate({"left": "-=" + movie_option_width * 4}, "slow", function() {
                    // check if the right end is reached
                    block_right = ($movie_container.css("left") === "-" + (movie_container_width - movie_carousel_width) + "px");
                    if (block_right) {
                        $next_button.addClass("blocked");
                        direction = "prev";
                    }
                });
                $genre_container.animate({"left": "-=" + genre_option_width}, "slow");
                $seeall_container.animate({"left": "-=" + genre_option_width}, "slow");
            }
            return false;
        });

        // put buttons into DOM
        $genre_carousel.prepend($prev_button);
        $genre_carousel.prepend($next_button);

        // stop rotating on hover
        $movie_container.bind("mouseenter",
                function() {
                    clearInterval(t);
                }).bind("mouseleave", function() {
                    t = window.setInterval(function() {
                        triggerCarousel(direction)
                    }, delay);
                });

        // fire counter
        t = window.setInterval(function() {
            triggerCarousel(direction)
        }, delay);

    } // if carousel
}; // carousel


/**
 * ratatingTeaser
 * @param config
 * TODO: clickable status indicator
 */
FM.ratatingTeaser = function(config) {
    var $teaser = $(config.selector);

    /**
     * counterController - updates counter and triggers showItem
     * @param i {Number} item index
     */
    function counterController(i) {
        counter--;

        // if counter went to 0
        if(counter < 1) {
            // set new counter
            counter = delay / 1000;

            // increment item index
            i++;

            // if out of range, start over from 0
            if(i >= items_length) {
                i = 0;
            }

            item_idx = i

            // show next item
            showItem(i);
        }
        
        // update counter text
        $teaser_counter.text(counter);
    }

    /**
     * showItem
     * @param i {Number} - item index
     */
    function showItem(i) {
        // show requested (i) item
        $teaser.find(".active").removeClass("active");
        $teaser.find("div").eq(i).addClass("active");

        // update status indicator
        $status.removeClass("a");
        $status.eq(i).addClass("a");
    }

    // init
    if($teaser.length > 0) {
        var t,
            $teaser_counter,
            $status,
            item_idx        = 0,
            counter         = 0,
            delay           = config.delay_sec * 1000 || 5000,
            items_length    = $teaser .children("div").length,
            status_template = '<div id="teaser-status" class="status"><div class="a"></div>'
                            + '<div></div><div></div><div></div><p id="teaser-counter"></p></div>'
        ;
        
        // append status indicator
        $teaser.append(status_template);
        $status = $("#teaser-status").find("div");
        
        // clickable status indicator
        $("#teaser-status").children("div").each(function(i) {
            $(this).bind("click", function() {
                counter = delay / 1000;
                $teaser_counter.text(counter);
                item_idx = i;
                showItem(i);
            });
        });

        // stop rotating on hover
        $teaser.bind("mouseenter", function() {
            clearInterval(t);
        }).bind("mouseleave", function() {
            t = window.setInterval(function() { counterController(item_idx) }, 1000);
        });
        
        // set counter value
        counter = delay / 1000;
        $teaser_counter = $("#teaser-counter");
        $teaser_counter.text(counter);

        // fire counter
        t = window.setInterval(function(){ counterController(item_idx) }, 1000);

    } // if teaser
}; // teaser

/**
 * showMoreList
 * @param config
 */
FM.showMoreList = function(config) {
    var list    = $(config.selector),
        msg     = config.msg || "rozwiń",
        limit   = config.limit || 10,
        roll    = $('<li><a href="#">' + msg + '</a></li>')
    ;

console.log("showMoreList: " + list);
    if(list.length > 0) {
        var lis = list.find("li"),
            length = lis.length
        ;

        // insert a roll down link and hide 
        if(length > 0) {
            for(var i = 0; i < length; i++) {
                if(i === limit) {
                    $(roll).insertAfter(lis[i]);
                } else if(i > limit) {
                    $(lis[i]).hide();
                }
            }
        }

        // bind hiding 
        roll.bind("click", function() {
            $(this).hide();
            for(var i = 0; i < length; i++) {
                $(lis[i]).show();
            }
            return false;
        });
    }
}; // showMoreList

FM.showAllScreenings = function(config) {
    var list    = $(config.selector),
        msgShow = config.msgShow || gettext("Show all screenings"),
        msgHide = config.msgHide || gettext("Hide screenings"),
        limit   = config.limit || 3,
        roll    = $('<li><a href="">' + msgShow + '</a></li>')
    ;
    if(list.length > 0) {
        list.each(function() {
        var childrenCount = list.find("ul.in-cinemas > li").length
        ;
        if(list.length > 0 && childrenCount > limit) {
            list.addClass("screenings");
            $(roll).appendTo(list);

            roll.bind("click", function() {
                if(list.hasClass("screenings")) {
                    list.removeClass("screenings");
                    roll.find("a").replaceWith('<a href="">' + msgHide + '</a>');
                } else {
                    list.addClass("screenings");
                    roll.find("a").replaceWith('<a href="">' + msgShow + '</a>');
                }
                return false;
            });
        }
    });
    }   
}

FM._prev_film_ids = function() {
    return $.map($('.rate-movie input.film-id'), function(i) {return $(i).val()}).join(',')
}

FM.rateMovieWidgetSmall = function(config) {
    var widget_selector = config.widget || 'body.rate-movies-page .rate-movie, body.home .join-us .rate-movie',
        true_widget_selector = config.widget || '.rate-movie > form',
        $widgets =  $(widget_selector),
        $true_widgets = $(true_widget_selector),
        rate_next_url = $( "#rate_next_film" ).attr( "href" )
    ;

    var replaceWidget = function( $widget ) {
        stop_timer($widget);
        $widget.unbind( 'mouseleave' )
               .unbind( 'mouseenter' )
               .css( "opacity", "1" )
               .stop()
               .animate({opacity: 0.3}, 2000);

        FM.rateNextAjax.add({
            type: "POST",
            url : rate_next_url,
            beforeCreate: function(xhr, opts) {
                opts.data = {prev_film_ids: FM._prev_film_ids()}
            },
            success: function( msg ) {
                $widget.html( msg )
                       .css( "opacity", "0.3" )
                       .stop()
                       .animate({opacity: 1}, 2000);

                FM.rateMovieWidgetSmall({ widget: $widget });
            },
            error: function() {
                $widget.css( "opacity", "0.3" )
                       .stop()
                       .animate({opacity: 1}, 2000);
            }

        });
    };

    function stop_timer($widget) {
        var id = $.data($widget, 'interval')
        if(id) clearInterval(id);
    }
    
    function start_timer($widget) {
        stop_timer($widget);
        var $timer = $widget.find('.timer');
        function setTimer() {
            if ( !FM.hasFocus ) return;
            var current = $.data( $widget, 'current-time' ) || 60;
            $.data( $widget, 'current-time', --current );
            $timer.html( current);
            if ( current <= 0 ) {
                $timer.html( '' );
                replaceWidget( $widget );
            }
        };
        if($timer.length)
            $.data($widget, 'interval', setInterval(setTimer, 1000))
    }

    if($true_widgets.length > 0) {
        $widgets.each(function(i) {
            var hoverable = !$($widgets[i]).hasClass("sr1"),
                $rating = $($widgets[i]).find(".rating-1"),
                $feature_rating = $($widgets[i]).find(".rating-3"),
                $this_widget = $($widgets[i]),
                movie_url = $this_widget.find(".movie").attr("href"),
                $ajax_loader = $this_widget.find(".ajax-loader"),
                $message = $this_widget.find("p.msg"),
                movie_title = $this_widget.find(".movie").html(),
                $timer = $this_widget.find('.timer'),
//                $timer = $( '<div class="timer"></div>' ).appendTo( $this_widget ),
                $rater = $this_widget.find('input[name=rater]').val()
            ;
            $this_widget.find('.skip-movie').click(function() {
                replaceWidget( $this_widget );
                return false;
            })
            // get movie id from movie url
            movie_url = (movie_url.slice(0, movie_url.length - 1));
            movie_url = (movie_url.slice(movie_url.lastIndexOf("/") + 1, movie_url.length));

            // stop counter when the cursor is on the widget
            $this_widget.bind( "mouseenter", function() {
                stop_timer($this_widget);
            }).bind( "mouseleave", function() {
                start_timer($this_widget);
            });

            // set interval
            start_timer($this_widget);

            /**
             * rate - submits ratings, updates stars look
             * @param stars - star widget collection
             * @param wv - star widget version
             */
            function rate(stars, wv) {
                // for each star widget
                stars.each(function(i) {
                    var $this_star = $(stars[i]),
                        current_rating = $this_star.prev("input").val() || 0,
                        new_rating = 0,
                        type_str = $this_star.prev("input").attr("id"),
                        type_desc = $this_star.prevAll("label").text(),
                        type = 1
                    ;

                    // get rating type
                    type = type_str.slice(type_str.indexOf("_", 6) + 1, type_str.length);

                    // change stars look on mouseover
                    $this_star.bind("mousemove", function(e) {
                        var width = this.clientWidth;
                        // read new rating
                        new_rating = (((e.clientX - $(this).offset().left) / (width) * 10) + 0.5).toFixed();
                        // change markup
                        $(this).attr("class", "rating-" + wv + " r" + new_rating);
                    }).bind("click", function() {
                        // clear interval if exists ...
                        stop_timer($this_widget);
                        // ... unbind start_timer on mouse leave
                        $this_widget.unbind("mouseleave")
                        // ... and bind mouseleave action
                        $this_widget._mouse_leaved = false;
                        $this_widget.bind( "mouseleave", function() {
                            $this_widget._mouse_leaved = true;
                        });

                        var put_url = "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/ratings/film/" + movie_url + "/" + type + "/";
                        // set new rating
                        current_rating = new_rating;
                        // change markup
                        $(this).attr("class", "rating-" + wv + " r" + new_rating);

                        hoverable = false;
                                
                        $ajax_loader.show();
                        
                        FM.ratingAjax.add({
                            type: "POST",
                            url:"/ajax/rate-film/",
                            data: {rating: new_rating, type:type, film_permalink:movie_url, rater:$rater},
                            success: function(msg) {
                                    $ajax_loader.hide();
                                    $message.text(gettext("Good job! ") + type_desc + gettext(" rated"))
                                            .css("opacity", "1")
                                            .stop()
                                            .animate({opacity: 0.5}, 1000);
                                    // step 1: rate movie -> rate in details
                                    if(type == 1) {
                                        if($this_widget.hasClass("sr1")) {
                                            $this_widget.removeClass("sr1").addClass("sr2").find("figcaption").append($this_star);
                                        }
                                    }
                                    
                                    if($this_star.text() === "") {
                                         $("body").trigger("rated");
                                    }

                                    $this_star.text("rated");

                                if ( $this_widget._mouse_leaved ) {
                                    replaceWidget( $this_widget );
                                } else {
                                    $this_widget.bind( "mouseleave", function() {
                                        replaceWidget( $this_widget );
                                    });
                                }
                            }
                        })
                    }).bind("mouseout", function() {
                        // change markup to reflect current rating
                        $(this).attr("class", "rating-" + wv + " r" + current_rating);
                    });
                })
            }

            rate($rating, 1);
            rate($feature_rating, 3);

            // step 2: rate in details -> write a short review
            $this_widget.find('div.rate-more p:first-child a').bind("click", function() {
                $this_widget.removeClass("sr2").addClass("sr3");
                $message.text("");
                return false;
            });

            // step 3
            // back: write a short review -> reate in details
            $this_widget.find('div.comment p:first-child a').bind("click", function() {
                $this_widget.removeClass("sr3").addClass("sr2");
                $message.text("");
                return false;
            });
            //forward: write a short review -> final screen
            $this_widget.find('.movie-short-review button').bind("click", function() {
                var put_url = "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/short-reviews/" + movie_url + "/";
                var comment = $this_widget.find(".movie-short-review textarea").val();
                if (comment.length < 10) {
                    $message.text(gettext("Review cannot be shorter than 10 characters!"))
                            .css("opacity", "1")
                            .stop()
                            .animate({opacity: 0.5}, 1000);
                    return false;
                }

                // submit short review
                $ajax_loader.show();
                $.ajax({
                    type: "PUT",
                    url: put_url,
                    data: {review_text: comment},
                    success: function(msg) {
                        var final_msg = gettext("<p>Thanks for rating <strong>") + movie_title + "</strong></p>" +
                                        gettext("<p>Your short review has appeared at ") + '<a href="' + $this_widget.find(".user-profile").val() + '">' + gettext("your profile page</a>'") + ".</p>"
                        console.log(msg);
                        $ajax_loader.hide();
                        $this_widget.removeClass("sr3").addClass("sr4");
                        $message.remove();
                        $this_widget.find(".final").append(final_msg);
                        $this_widget.find(".rating-1").hide();
                    }
                });
                this.disabled = true;
                return false;
            });

            // rate next movie
            $this_widget.find("p.rate-next a").bind("click", function() {
                var url =  $(this).attr("href") + "ajax-rating/";
                // get random movie to rate
                $ajax_loader.show();
                FM.ratingAjax.add({
                    type: "POST",
                    url: url,
                    beforeCreate: function(xhr, opts) {
                        opts.data = {prev_film_ids: FM._prev_film_ids()}
                    },
                    success: function(msg) {
                        console.log(msg);
                        $ajax_loader.hide();
                        $this_widget.html(msg);
                        $this_widget.attr("class", "rate-movie sr1");
                        FM.rateMovieWidgetSmall({widget: $this_widget});
                    }
                });
                return false;
            });

            // filmbasket actions DRY
            function filmbasket(config) {
                hoverable = false;
                $ajax_loader.show();
                $.ajax({
                    type: "PUT",
                    url: config.put_url,
                    data: config.data,
                    success: function(msg) {
                        console.log(msg);
                        $ajax_loader.hide();
                        $this_widget.removeClass("sr1").addClass("sr4");
                        $message.remove();
                        $this_widget.find(".final").append(config.final_msg);
                        $this_widget.find(".rating-1").hide();
                    }
                });
            }

            // add to whish list
            $this_widget.find(".whishlist").bind("click", function() {
                filmbasket({
                    put_url: "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/filmbasket/" + movie_url + "/",
                    data: { wishlist: 1 },
                    final_msg: gettext("<p>You've added <strong>") + movie_title +
                            "</strong> " + gettext("to_your_wishlist") + ' <a href="' + $(this).attr("href") + '">' + gettext("wishlist</a>") +
                            gettext("</p><p>You can send your wishlist to your friends so that they know what to get you or what to bring to your place for a movies night.</p>")
                });
                return false;
            });

            // add to shit list
            $this_widget.find(".shitlist").bind("click", function() {
                filmbasket({
                    put_url: "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/filmbasket/" + movie_url + "/",
                    data: { wishlist: 9 },
                    final_msg: gettext("<p>You've added <strong>") + movie_title +
                            '</strong> ' + gettext("to_your_shitlist") + ' <a href="' + $(this).attr("href") + '">' + gettext("shitlist</a>") +
                            gettext("</p><p>We won't be showing you this movie again.</p>")
                });
                return false;
            });

        }); // each widget
    }
}; // rateMovie

FM.rateMovieWidgetSimple = function() {
    var $widgets = $("body:not(.rate-movies-page) .rate-movies-simple, ol.ranking-movies").find(".rate-movie-simple");
    if($widgets.length > 0) {
        $widgets.each(function(i) {
            var $this_widget = $($widgets[i]),
                $this_star = $this_widget.find(".rating-1"),
                $ajax_loader = $this_widget.find(".ajax-loader"),
                $x = $('<span title="' + gettext("Remove your rating") + '" class="x">'),
                $message = $this_widget.find("p.msg"),
                $movie_a = $this_widget.find(".t"),
                movie_url = $movie_a.attr("href"),
                movie_title = $movie_a.text(),
                current_rating = $this_star.prevAll("input").val() || 0,
                new_rating = 0,
                type = 1,
                put_url
            ;
            if(!movie_url) return;
            // get movie id from movie url
            movie_url = (movie_url.slice(0, movie_url.length - 1));
            movie_url = (movie_url.slice(movie_url.lastIndexOf("/") + 1, movie_url.length));

            put_url = "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/ratings/film/" + movie_url + "/" + type + "/";
            
            // change stars look on mouseover
            $this_star.bind("mousemove", function(e) {
                var width = this.clientWidth;
                // read new rating
                new_rating = (((e.clientX - $(this).offset().left) / (width) * 10) + 0.5).toFixed();
                // change markup
                $(this).attr("class", "rating-1 r" + new_rating);
            }).bind("click", function() {
                $ajax_loader.css("display", "block");
                    $this_star.parent().find('input[type=text]').val(new_rating).attr('value', new_rating)
                    // submit user's rating
                    FM.ratingAjax.add({
                        type: "POST",
                        url:"/ajax/rate-film/",
                        data: {rating: new_rating, type:type, film_permalink:movie_url},
                        success: function(msg) {
                            console.log(msg)
                            $ajax_loader.hide();
                            $message.text(gettext("Good job! Movie rated"))
                                    .css("opacity", "1")
                                    .stop()
                                    .animate({opacity: 0.5}, 2000);
                            
                            if(!current_rating)
                                $("body").trigger("rated");

                            // insert remove rating button
                            if(!current_rating && type != 0) {
                                $this_star.after($x);
                            }
                            // set new rating
                            current_rating = new_rating;
                            // change markup
                            $this_star.attr("class", "rating-1 r" + current_rating);
                        }
                    })
/*                    $.ajax({
                        type: "PUT",
                        url: put_url,
                        data: {rating: new_rating },
                        success: function(msg) {
                            console.log(msg);
                            $ajax_loader.hide();
                            $message.text(gettext("Good job! Movie rated"))
                                    .css("opacity", "1")
                                    .stop()
                                    .animate({opacity: 0.5}, 2000);
                            // insert remove rating button
                            if(!current_rating && type != 0) {
                                $this_star.after($x);
                            }
                            // set new rating
                            current_rating = new_rating;
                            // change markup
                            $(this).attr("class", "rating-1 r" + new_rating);
                        }
                    });*/
            }).bind("mouseout", function() {
                // change markup to reflect current rating
                $(this).attr("class", "rating-1 r" + current_rating);
            });

            // remove rating
            $this_star.parent().delegate(".x", "click", function() {
                var $this_x = $(this)
                ;
                $ajax_loader.show();
                $.ajax({
                    type: "DELETE",
                    url: put_url,
                    success: function(msg) {
                        console.log(msg);
                        $this_star.attr("class", "rating-1 r0");
                        $this_x.remove();
                        current_rating = 0;
                        $ajax_loader.hide();
                        $message.text(gettext("Movie rating removed"))
                                .css("opacity", "1")
                                .stop()
                                .animate({opacity: 0.5}, 1000);
                    }
                });
            });

            // add to whishlist
            $this_widget.find(".whishlist").bind("click", function() {
                var $a = $(this)
                ;
                $ajax_loader.show();
                $.ajax({
                    type: "PUT",
                    url: "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/filmbasket/" + movie_url + "/",
                    data: { wishlist: 1 },
                    success: function(msg) {
                        console.log(msg);
                        if($this_widget.parents(".movie-list.Shitlist").length) {
                            $this_widget.parent("li").slideUp("slow");
                        } else {
                        $message.html(
                                    gettext("Movie added to your ") +
                                    '<a href="' + $a.attr("href") + '">' +
                                    gettext("wishlist</a>"))
                                .css("opacity", "1")
                                .stop()
                                .animate({opacity: 0.5}, 2000);
                        }
                        $ajax_loader.hide();
                    }
                });
                return false;
            });

            // add to shitlist
            $this_widget.find(".shitlist").bind("click", function() {
                var $a = $(this)
                ;
                $ajax_loader.show();
                $.ajax({
                    type: "PUT",
                    url: "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/filmbasket/" + movie_url + "/",
                    data: { wishlist: 9 },
                    success: function(msg) {
                        if($this_widget.parents(".movie-list.Wishlist").length) {
                            $this_widget.parent("li").slideUp("slow");
                        } else {
                            $message.html(
                                        gettext("Movie added to your ") +
                                        '<a href="' + $a.attr("href") + '">' +
                                        gettext("shitlist</a>"))
                                    .css("opacity", "1")
                                    .stop()
                                    .animate({opacity: 0.5}, 2000);
                        }
                        $ajax_loader.hide();
                    }
                });
                return false;
            });

            // remove from the list
/*
            $this_widget.find("button.remove").bind("click", function() {
                var $a = $(this),
                    put_data
                ;
                if($this_widget.parents(".movie-list.Wishlist").length || $this_widget.parents(".movie-list.Shitlist").length) {
                    put_data = {
                        wishlist: 0
                    }
                } else {
                    put_data = {
                        owned: 0
                    }
                }
                $ajax_loader.show();
                $.ajax({
                    type: "PUT",
                    url: "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/filmbasket/" + movie_url + "/",
                    data: put_data,
                    success: function(msg) {
                        $this_widget.parent("li").slideUp("slow");
                        $ajax_loader.hide();
                    }
                });
                return false;
            });
*/
        });
    }
};

FM.ratingWidget = function() {
    var $widgets = $(".rating-widget");
    if($widgets.length > 0) {
        $widgets.each(function(i) {
            var $this_widget = $($widgets[i]),
                $this_star = $this_widget.find(".rating-1"),
                $rating_input = $this_star.parent().find('input[type=text]'),
                $ajax_loader = $this_widget.find(".ajax-loader"),
                $x = $('<span title="' + gettext("Remove your rating") + '" class="x">'),
                $message = $this_widget.find("p.msg"),
                current_rating = $rating_input.val() || 0,
                new_rating = 0,
                type=$this_widget.find('input[name$=-type]').val();

            function post_form(opts) {
                $ajax_loader.show();
                FM.ratingAjax.add({
                    type: "POST",
                    url:"/ajax/process-ratings/",
                    data: $this_widget.find('input').fieldSerialize(),
                    success: function(msg) {
                        $ajax_loader.hide();
                        return opts.success(msg);
                    }
                })
            }

            // change stars look on mouseover
            $this_star.bind("mousemove", function(e) {
                var width = this.clientWidth;
                // read new rating
                new_rating = (((e.clientX - $(this).offset().left) / (width) * 10) + 0.5).toFixed();
                // change markup
                $(this).attr("class", "rating-1 r" + new_rating);
            }).bind("click", function() {
                    var rating = new_rating;
                    $rating_input.val(rating).attr('value', rating)
                    // submit user's rating
                    post_form({
                        success: function(msg) {
                            $message.text(gettext("Good job! Movie rated"))
                                    .css("opacity", "1")
                                    .stop()
                                    .animate({opacity: 0.5}, 2000);
                            
                            if(!current_rating) {
                                $("body").trigger("rated", [type, $this_widget]);
                                $this_star.after($x);
                            }

                            current_rating = rating;
                            // change markup
                            $this_star.attr("class", "rating-1 r" + current_rating);
                        }
                    })
            }).bind("mouseout", function() {
                // change markup to reflect current rating
                $(this).attr("class", "rating-1 r" + current_rating);
            });

            // remove rating
            $this_star.parent().delegate(".x", "click", function() {
                var $this_x = $(this)
                $rating_input.val("").attr("value", "")
                post_form({
                    success: function(msg) {
                        $this_star.attr("class", "rating-1 r0");
                        $this_x.remove();
                        current_rating = 0;
                        $message.text(gettext("Movie rating removed"))
                                .css("opacity", "1")
                                .stop()
                                .animate({opacity: 0.5}, 1000);
                    }
                });
            });
            $this_star.parents('form').find('input[type=submit], input[type=text]').hide()
       });
    }
};

FM.RATING_TOOLTIPS = {
    1 : gettext( 'disaster' ),
    2 : gettext( 'very bad' ),
    3 : gettext( 'poor' ),
    4 : gettext( 'below average' ),
    5 : gettext( 'average' ),
    6 : gettext( 'above average' ),
    7 : gettext( 'good' ),
    8 : gettext( 'very good' ),
    9 : gettext( 'exceptional' ),
    10: gettext( 'masterpiece' )
};

/**
 * rateMovie widget
 * @param config
 */
FM.rateMovieWidget = function(config) {
    var widget_selector = config.widget || 'body:not(.rate-movies-page, .home) .rate-movie',
        true_widget_selector = config.widget || '.rate-movie > form',
        $widgets =  $(widget_selector),
        $true_widgets = $(true_widget_selector)
    ;

    if($true_widgets.length > 0) {
        $widgets.each(function(i) {
            var hoverable = !$($widgets[i]).hasClass("s1"),
                $rating = $($widgets[i]).find(".rating-1"),
                $feature_rating = $($widgets[i]).find(".rating-3"),
                $this_widget = $($widgets[i]),
                movie_url = $this_widget.find(".movie").attr("href"),
                $ajax_loader = $this_widget.find(".ajax-loader"),
                $message = $this_widget.find("p.msg"),
                movie_id = $this_widget.find(".film-id").val(),
                movie_title = $this_widget.find(".movie").html(),
                $tooltip = $($widgets[i]).find(".rating-tooltip"),
                $x = $('<span title="' + gettext("Remove your rating") + '" class="x">')
            ;

            // get movie id from movie url
            movie_url = (movie_url.slice(0, movie_url.length - 1));
            movie_url = (movie_url.slice(movie_url.lastIndexOf("/") + 1, movie_url.length));

            // hover
            $this_widget.hover(
                function() {
                    if(hoverable) {
                        $(this).addClass("s1");
                    }
                },
                function() {
                    if(hoverable) {
                        $(this).removeClass("s1");
                    }
                }
            );

            /**
             * updates others-ratings widget if exists
             * 
             */
            var updateOthersRatings = function() {
                var others_rating_url = "/ajax/widget/movie/film_others_ratings/?film_id=" + movie_id,
                others_rating_selector = "section.others-ratings > *";

                $( "section.others-ratings" ).load(  others_rating_url + " " + others_rating_selector, function() {
                    FM.loadAjaxWidgets();
                });
            };

            /**
             * rate - submits ratings, updates stars look
             * @param stars - star widget collection
             * @param wv - star widget version
             */
            function rate(stars, wv) {
                var master_rating = ( wv == 1 );

                // for each star widget
                stars.each(function(i) {
                    var $this_star = $(stars[i]),
                        current_rating = $this_star.prevAll("input").val() || 0,
                        new_rating = 0,
                        type_str = $this_star.prevAll("input").attr("id"),
                        type_desc = $this_star.prevAll("label").text(),
                        type = 1,
                        put_url,
                        $star_container
                    ;

                    // get rating type
                    type = type_str.slice(type_str.indexOf("_", 6) + 1, type_str.length);
                    put_url = "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/ratings/film/" + movie_url + "/" + type + "/";

                    // change stars look on mouseover
                    $this_star.bind("mousemove", function(e) {
                        var width = this.clientWidth;
                        // read new rating
                        new_rating = (((e.pageX - $(this).offset().left) / (width) * 10) + 0.5).toFixed();
                        //console.log( 'width: ' + width + ', offset: ' + $( this ).offset().left + ', e.clientX: ' + e.clientX + ', e.pageX: ' + e.pageX )
                        // change markup
                        $(this).attr("class", "rating-" + wv + " r" + new_rating);

                        if( master_rating ) {
                            $tooltip.html( FM.RATING_TOOLTIPS[new_rating] || '' );
                        }
                    }).bind("click", function() {
                        hoverable = false;
                        $ajax_loader.show();
                        // submit user's rating
                        var rating_to_save = new_rating;
                        FM.ratingAjax.add({
                            type: "POST",
                            url:"/ajax/rate-film/",
                            data: {rating: rating_to_save, type:type, film_permalink:movie_url},
                            success: function(msg) {
                                    console.log(msg);
                                    $ajax_loader.hide();
                                    $message.text(gettext("Good job! ") + type_desc + gettext(" rated"))
                                            .css("opacity", "1")
                                            .stop()
                                            .animate({opacity: 0.5}, 1000);
                                    // step 1: rate movie -> rate in details
                                    if(type == 1) {
                                        if($this_widget.hasClass("s1")) {
                                            $this_widget.removeClass("s1").addClass("s2").find("figcaption").append($this_star, $tooltip, $x);
                                        }
                                    }
                                    // insert remove rating button
                                    if(!current_rating && type != 0) {
                                        $this_star.after($x.html(''));
                                    }
                                    // set new rating
                                    if(!current_rating)
                                        $("body").trigger("rated");
                                    current_rating = rating_to_save;
                                    // update stars
                                    $this_star.attr("class", "rating-" + wv + " r" + current_rating );
                                    if( master_rating ) {
                                        $tooltip.html( FM.RATING_TOOLTIPS[current_rating] || '' );
                                        updateOthersRatings();
                                    }
                            }
                        })
                        /*
                            $.ajax({
                                type: "PUT",
                                url: put_url,
                                data: {rating: new_rating },
                                success: function(msg) {
                                    console.log(msg);
                                    $ajax_loader.hide();
                                    $message.text(gettext("Good job! ") + type_desc + gettext(" rated"))
                                            .css("opacity", "1")
                                            .stop()
                                            .animate({opacity: 0.5}, 1000);
                                    // step 1: rate movie -> rate in details
                                    if(type == 1) {
                                        if($this_widget.hasClass("s1")) {
                                            $this_widget.removeClass("s1").addClass("s2").find("figcaption").append($this_star, $x);
                                        }
                                    }
                                    // insert remove rating button
                                    if(!current_rating && type != 0) {
                                        $this_star.after($x);
                                    }
                                    // set new rating
                                    current_rating = new_rating;
                                    // update stars
                                    $(this).attr("class", "rating-" + wv + " r" + new_rating);
                                }
                            });
                        */
                    }).bind("mouseout", function() {
                        // change markup to reflect current rating
                        $(this).attr("class", "rating-" + wv + " r" + current_rating);
                        
                        if( master_rating ) {
                            $tooltip.html( FM.RATING_TOOLTIPS[current_rating] || '' )
                        }
                    });

                    // remove rating
                    $star_container = $this_star.parent();
                    if(type == 1) {
                        $star_container = $this_widget.find("figcaption").add($star_container);
                    }
                    $star_container.delegate(".x", "click", function() {
                        var $this_x = $(this)
                        ;
                        $ajax_loader.show();
                        $.ajax({
                            type: "DELETE",
                            url: put_url,
                            success: function(msg) {
                                console.log(msg);
                                $this_star.attr("class", "rating-" + wv + " r0");
                                $( ".x", $this_widget ).remove();
                                current_rating = 0;
                                $ajax_loader.hide();
                                $tooltip.html( '' );
                                $message.text(type_desc + gettext(" rating removed"))
                                        .css("opacity", "1")
                                        .stop()
                                        .animate({opacity: 0.5}, 1000);

                                $this_widget.removeClass( "s2" ).removeClass( "s3" ).addClass( "s1" ).find( 'p.rate' ).append( $rating, $tooltip );
                                updateOthersRatings();
                            }
                        });
                    });
                    
                    // set text on hover
                    if( master_rating ) {
                        $star_container.delegate(".x", "mouseover", function() { $( this ).html( gettext( 'remove my ratings' ) ); });
                        $star_container.delegate(".x", "mouseout", function() { $( this ).html( '' ); });
                    }
                }); // rate
            }

            rate($rating, 1);
            rate($feature_rating, 3);

            // movie rated? -> step 1: rate in details
            if($this_widget.hasClass("s1") && $this_widget.find("p.rate input").val()) {
                $this_widget.removeClass("s1").addClass("s2").find("figcaption").append($rating, $tooltip, $x);
            }

            // step 2: rate in details -> write a short review
            $this_widget.find('div.rate-more p:first-child a').bind("click", function() {
                $this_widget.removeClass("s2").addClass("s3");
                $message.text("");
                return false;
            });

            // step 3
            // back: write a short review -> reate in details
            $this_widget.find('div.comment p:first-child a').bind("click", function() {
                $this_widget.removeClass("s3").addClass("s2");
                $message.text("");
                return false;
            });
            
            // add limit indicator
            var limit = 1000;
            var $textarea = $this_widget.find(".movie-short-review textarea");
            var text_length = $textarea.val().length;
            var $limit_indicator = $( '<div class="limit">' + limit + '</div>' )
                        .appendTo( $this_widget.find( '.movie-short-review' ) )

            $limit_indicator.text(limit - text_length);
            if(text_length > limit) {
                $limit_indicator.addClass("exceded");
            }
            
            // custom char limiter
            $textarea.keyup(function() {
                var text = this.value;
                text_length = text.length;

                if(text_length > limit) {
                    // this.value = text.substr(0, limit);
                    text_length = this.value.length;
                    $limit_indicator.addClass("exceded")
                                    .css("opacity", "0")
                                    .stop()
                                    .animate({opacity: 1}, 1000);

                } else {
                    $limit_indicator.removeClass("exceded");
                }
                $limit_indicator.text(limit - text_length);
            });

            //forward: write a short review -> final screen
            $this_widget.find('.movie-short-review button').bind("click", function() {
                var put_url = "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/short-reviews/" + movie_url + "/";
                var comment = $this_widget.find(".movie-short-review textarea").val();
                if (comment.length < 10 || comment.length > limit ) {
                    $message.text( ( comment.length > limit ) ? gettext("Review cannot be longer than 1000 characters!") : gettext("Review cannot be shorter than 10 characters!") )
                            .css("opacity", "1")
                            .stop()
                            .animate({opacity: 0.5}, 1000);
                    return false;
                }
                var $button = this;
                // submit short review
                $ajax_loader.show();
                $message.text( '' );
                $button.disabled = true;
                $.ajax({
                    type: "PUT",
                    url: put_url,
                    data: {review_text: comment},
                    success: function(msg) {
                        var final_msg = gettext("<p>Thanks for rating <strong>") + movie_title + "</strong></p>" +
                                        gettext("<p>Your short review has appeared at ") + '<a href="' + $this_widget.find(".user-profile").val() + '">' + gettext("your profile page</a>'") + ".</p>"
                        console.log(msg);
                        $ajax_loader.hide();
                        $this_widget.removeClass("s3").addClass("s4");
                        $message.remove();
                        $this_widget.find(".final").append(final_msg);
                        $this_widget.find(".rating-1").hide();
                    }, error: function( error ) {
                        var message;
                        try {
                            var result = jQuery.parseJSON( error.responseText );
                            message = result.review_text[0];

                        } catch( e ) {
                            console.log( e )
                            message = gettext( 'Something goes wrong, please try again later' );
                        }
                        $ajax_loader.hide();
                        $button.disabled = false;
                        $message.text( message )
                            .css( "opacity", "1" )
                            .stop()
                            .animate( { opacity: 0.5 }, 1000 );
                    }
                });

                return false;
            });

            // rate next movie
            $this_widget.find("p.rate-next a").bind("click", function() {
                var url =  $(this).attr("href") + "ajax-rating/";
                // get random movie to rate
                $ajax_loader.show();
                FM.ratingAjax.add({
                    type: "POST",
                    url: url,
                    beforeCreate: function(xhr, opts) {
                        opts.data = {prev_film_ids: FM._prev_film_ids()}
                    },
                    success: function(msg) {
                        console.log(msg);
                        $ajax_loader.hide();
                        $this_widget.html(msg);
                        $this_widget.attr("class", "rate-movie s1");
                        FM.rateMovieWidget({widget: $this_widget});
                    }
                });
                return false;
            });

            // filmbasket actions DRY
            function filmbasket(config) {
                hoverable = false;
                $ajax_loader.show();
                $.ajax({
                    type: "PUT",
                    url: config.put_url,
                    data: config.data,
                    success: function(msg) {
                        console.log(msg);
                        $ajax_loader.hide();
                        $this_widget.removeClass("s1").addClass("s4");
                        $message.remove();
                        $this_widget.find(".final").append(config.final_msg);
                        $this_widget.find(".rating-1").hide();
                    }
                });
            }

            // add to whish list
            $this_widget.find(".whishlist").bind("click", function() {
                filmbasket({
                    put_url: "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/filmbasket/" + movie_url + "/",
                    data: { wishlist: 1 },
                    final_msg: gettext("<p>You've added <strong>") + movie_title +
                            "</strong> " + gettext("to_your_wishlist") + ' <a href="' + $(this).attr("href") + '">' + gettext("wishlist</a>") +
                            gettext("</p><p>You can send your wishlist to your friends so that they know what to get you or what to bring to your place for a movies night.</p>")
                });
                return false;
            });

            // add to shit list
            $this_widget.find(".shitlist").bind("click", function() {
                filmbasket({
                    put_url: "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/filmbasket/" + movie_url + "/",
                    data: { wishlist: 9 },
                    final_msg: gettext("<p>You've added <strong>") + movie_title +
                            '</strong> ' + gettext("to_your_shitlist") + ' <a href="' + $(this).attr("href") + '">' + gettext("shitlist</a>") +
                            gettext("</p><p>We won't be showing you this movie again.</p>")
                });
                return false;
            });

        }); // each widget
    }
}; // rateMovie


FM.addToCollection = function(config) {
	var widget_selector = config.widget || '',
		true_widget_selector = config.widget || '',
		$widgets =  $(widget_selector),
		$true_widgets = $(true_widget_selector)
	;
	if($true_widgets.length > 0) {
		$widgets.each(function(i) {
			var $this_widget = $($widgets[i]),
				$widget_button = $this_widget.find("input[type='submit']"),
				owned = $this_widget.find("input[type='submit']").hasClass("active") ? 1 : null,
				movie_url = $this_widget.find("input.permalink").val();
			;
			function filmbasket(config) {
				$.ajax({
					async: true,
					type: "PUT",
					url: config.put_url,
					data: config.data,
					success: function(msg) {
						console.log(msg);
					}
				});
			}

			// add to collection
			$this_widget.bind("submit", function(event) {
				event.preventDefault();
				filmbasket({
					put_url: "http://" + location.host + "/api/" + FM.API_VERSION + "/profile/filmbasket/" + movie_url + "/",
					data: { owned: owned }/*,
					final_msg: gettext("<p>You've added <strong>") + movie_title + "</strong> " + gettext("to your") + '<a href="' + $(this).attr("href") + '">' + gettext("collection</a>") + gettext("</p>")*/
				});
				console.log("owned:" + owned);
			});
		});
	}
};


/**
 * trailers - binds toplayer for movie trailers
 */
FM.trailers = function() {
    var trailers = $("section.trailer, section.trailers").find(".v"),
        triggers = $(trailers).prev()
    ;

    $(trailers).each(function(i) {
        var $trigger = $(triggers[i]);

        $trigger.bind("click", function() {
            var content = $( trailers[i] );
            var contents = content.contents()
            if ( contents.length <= 2 && contents[0].nodeType == Node.TEXT_NODE ) {
                var href = contents[0].nodeValue;
                content = $( '<div><p id="video-content"><a href="' + href + '">' + href + '</a></p></div>' );
                if ( contents.length == 2 ) {
                    content.append( contents[1] );
                }
                content = content.html();
            } else {
                content = '<div id="video-content">' + content.html() + '</div>';
            }

            FM.toplayer({
                headline: $trigger.attr("title"),
                content : content,
                width   : '560'
            });

            // bind remove button
            var $info_message = $( '<div class="info-message"></div>' )
                                    .hide()
                                    .appendTo( $( "#toplayer") );

            var $remove_button = $( "#toplayer a.remove-trailer" );
            $remove_button.removeVideo({
                onLoad   : function( $e ) {
                    this.disabled = true;
                    $info_message
                        .html( '' )
                        .addClass( 'loading' )
                        .show();
                },
                onSuccess: function( m ) {
                    if ( !m.need_moderate ) {
                        $.closeTopLayer();

                        var $el = $trigger.parent();
                        $el.animate( { opacity: 0. }, 1000, function() {
                            $el.slideUp( "slow" );
                        });
                        // ..
                        return false;
                    }
                    
                    $( "#toplayer #video-content" ).hide();
                    $remove_button.hide();
                    $info_message.hide();
                    
                    var $content = $( '<p>' + m.message + '</p>')
                                    .appendTo( $( '#toplayer' ) );

                    var height = $content.height();
                    var position_top = $( "#toplayer" ).position().top - height / 2;
                    position_top = position_top < 0 ? '0px' : position_top + 'px';

                    $( '#toplayer' ).css( 'top', position_top );

                },
                onError  : function( m ) {
                    $info_message
                        .removeClass( 'success' )
                        .removeClass( 'loading' )
                        .addClass( 'error' )
                        .html( "Oops... something went wrong :( Please accept our apologies." )
                        .fadeIn();
                }
            });

            return false;
        });
    });
};

/**
 * toplayer
 * @param config
 *
 * TODO: layer height > scroll offset
 * TODO: change position on window resize
 * TODO: ? follow the scroll
 * TODO: get rid of close_selectors, use .close instead
 * TODO: reuse appended markup
 */
FM.toplayer = function(config) {
    var headline        = config.headline || '',
        content         = config.content || '',
        width           = config.width || '310',
        close_label     = config.close_label || 'Close',
        position_left   = 0,
        position_top    = 0,
        scroll_top      = 0,
        close_selectors = config.close_selectors || [],
        template        = $('<div></div>'),
        overlay         = $('<div id="overlay"></div>'),
        close_btn       = $('<a title="' + close_label + '" class="close" href="#">X</a>'),
        toplayer        = $('<div id="toplayer"><h1>' + headline + '</h1>' + content + '</div>')
    ;

    // close toplayer
    function close_toplayer() {
        $("#toplayer").remove();
        $("#overlay").remove();
        
        $( document ).unbind( 'keydown.toplayer' )
        return false;
    }

    // set horizontal position and width
    position_left = (($(window).width() - width) / 2);
    position_left = (position_left < 0) ? '0px' : position_left + 'px';
    $(toplayer).css('left', position_left);
    $(toplayer).width(width);

    // assmeble and put into DOM
    toplayer.append(close_btn);
    template.append(overlay);
    template.append(toplayer);
    $('body').append($(template).html());

    // set vertical position
    scroll_top = (window.pageYOffset) ? window.pageYOffset : document.documentElement.scrollTop;
    position_top = (scroll_top + ($(window).height() - $("#toplayer").height()) / 2);
    position_top = (position_top < 0) ? '0px' : position_top + 'px';
    $('#toplayer').css('top', position_top);

    // areas that close toplayer
    $('#overlay').bind('click', close_toplayer);
    $('#toplayer .close').bind('click', close_toplayer);

    // links in content that close toplayer
    toplayer = $('#toplayer');
    if(close_selectors.length > 0) {
        for(var i = 0; i < close_selectors.length; i++) {
            toplayer.delegate("'" + close_selectors[i] + "'", 'click', close_toplayer);
        }
    }
    
    // bind keys
    $( document ).bind( 'keydown.toplayer', function(e) {
        if ( e.keyCode == 27 ) { // close on escape
            e.preventDefault();
            close_toplayer();
        }
    });
}; // toplayer

FM.flashMessages = function() {
    var $container = $("#messages");

    $container.append("<button>" + gettext("Close") + "</button>");
    $container.find("button").bind("click", function() {
        $(this).parent(".flash-messages").slideUp("slow");
    });
};

FM.toggleFilter = function(config) {
    var $filter = $("#filter-form");
    if($filter.length > 0) {
        var $show_filter_options,
            $form_text_inputs = $($filter).find('form input:text'),
            form_filled = false,
            show_filter_label = config.show_filter_label || gettext("Movie filtering options")
        ;

        // append buttons
        $filter.append('<button class="x">Close</button>');
        $filter.before('<button class="toggle-filter" id="show-filter-options">' + show_filter_label + '</button>');

        $show_filter_options = $("#show-filter-options");

        // check if the filter form has been filled in
        for(var i = 0; i < $form_text_inputs.length; i++) {
            if($form_text_inputs[i].value !== "") {
                form_filled = true;
                break;
            }
        }

        if(!form_filled && $filter.find(".rating-options").length) {
            form_filled = $filter.find(".rating-options > ul > li > strong")
                                 .not(".rating-options > ul > li:first-child > strong").length || form_filled;
        }

        // hide filter form on default when it has not been used
        if(!form_filled) {
            $filter.hide();
        } else {
            $show_filter_options.hide();
        }
        
        $show_filter_options.bind("click", function() {
            $show_filter_options.hide();
            $filter.slideDown("slow");
        });
        
        $filter.find("button").bind("click", function() {
            $filter.slideUp("slow", function() {
                $show_filter_options.show();
            });
        });
    }
};

FM.wallPost = function() {
    var $wall_form = $("#wall-form"),
             $wall = $( "#wall" );

    if($wall_form.length) {
        var $ajax_loader = $('<span class="ajax-loader"></span>'),
            $submit_button = $wall_form.find("button"),
            $textarea = $("#id_text"),
            limit = $textarea.attr("maxlength"),
            $limit_indicator = $("#wall-post-char-limit"),
            text_length = $textarea.val().length
        ;

        // expand textarea while typing
        $textarea.autogrow();

        // update char limit indicator (for page refreshes with non-empty textarea value)
        $limit_indicator.text(limit - text_length);
        if(text_length > limit) {
            $limit_indicator.addClass("exceded");
        }
        // remove maxlength attr
        $textarea.removeAttr("maxlength");

        // custom char limiter
        $textarea.keyup(function() {
            var text = this.value
            ;
            text_length = text.length;

            if(text_length > limit) {
                // this.value = text.substr(0, limit);
                text_length = this.value.length;
                $limit_indicator.addClass("exceded")
                                .css("opacity", "0")
                                .stop()
                                .animate({opacity: 1}, 1000);

            } else {
                $limit_indicator.removeClass("exceded");
            }
            $limit_indicator.text(limit - text_length);
        });

        $ajax_loader.insertAfter($submit_button);
        $submit_button.bind("click", function() {
            var wall_post_text = $textarea.val();

            $ajax_loader.css("display", "block");
            $( '.wallpost-errors' ).remove();

            $.ajax({
                type: "POST",
                url: "?ajax",
                data: {
                    text: wall_post_text
                },
                success: function( msg ) {
                    $ajax_loader.hide();
                    
                    // if response is json display errors
                    try {
                        var result = jQuery.parseJSON( msg );
                        if ( !result.success ) {
                            for ( var key in result.errors ) {
                                var $errorlist = $( '<ul class="wallpost-errors errorlist"><ul>' ).hide();
                                for ( var i = 0; i < result.errors[key].length; i++ ) {
                                    $errorlist.append( '<li>' + result.errors[key][i] + '</li>' );
                                }
                                $errorlist.prependTo( $wall_form ).fadeIn();
                            }
                        }
                    
                    } catch ( e ) {
                        var $tmp = $("<div></div>"),
                            $post
                        ;
                        $tmp.html(msg);
                        $post = $tmp.find("section");
                        $post.hide();
                        
                        // update new wallpost publish time
                        jQuery( "time.timeago", $post ).timeago();

                        $("#wall").prepend($post);
                        $post.slideDown("slow");
                        $textarea.val("");
                        $limit_indicator.text(limit);
                    }
                }
            });
            return false;
        });
    }
    
    // edit wallpost
    $wall.delegate( ".edit-wallpost", "click", function() {

        var $a          = $( this ),
            $form       = $( '<form class="wf">' +
                               '<textarea cols="40" rows="3"></textarea>' + 
                               '<button class="btn">OK</button> ' + gettext( 'or' ) + ' ' +
                               '<a class="cancel" href="#">' + gettext( 'Cancel' ) + '</a>' +
                               '<span class="ajax-loader"></span>' +
                             '</form>' )
                             .hide(),

            $button      = $form
                             .find("button")
                             .css( 'margin-right','5px' ),
   
            $p           = $a
                             .parents("footer")
                             .parent()
                             .find(".wallpost-body"),

            $ajax_loader = $form
                             .find(".ajax-loader"),

            $cancel      = $form
                             .find( "a.cancel" ),

            $textarea    = $form
                             .find("textarea"),

            object_uri   = $( this )
                             .attr("rel"),

            $error       = $( '<p class="errorlist"></p>' )
                             .hide()
                             .appendTo( $a.parents( 'footer' ) )
        ;

        $form.insertAfter( $p );

        $.getJSON( "http://" + location.host + "/api" + object_uri, function( data ) {
            $textarea.val( data.review_text )
            $textarea.autogrow();

            $p.slideUp( "slow", function() {
                $form.slideDown( "slow" );
                $a.hide();
            });
        });

        $cancel.bind( "click", function() {
            $form.slideUp( "slow", function() {
                $p.slideDown( "slow" );
                $form.remove();
                $a.show();
            });
            // ..
            return false;
        });

        $button.bind("click", function() {
            $ajax_loader.show();
            $error.hide();
            $.ajax({
                type: "PUT",
                url : "http://" + location.host + "/api" + object_uri,
                data: {
                    review_text: $textarea.val()
                },
                success: function( msg ) {
                    var update_review = function( m ) {
                        $ajax_loader.hide();
                        $p.html( m );
                        $cancel.click();
                    };
                    // try fetch rendered review ...
                    $.ajax({
                        type: 'GET',
                        url : '/ajax/render-wallpost/' + $a.attr( 'href' ).replace( '#edit-', '' ),
                        success: update_review,
                        error  : function( e ) {
                            console.log( 'error fetching rendered review, need to set raw ... ', e );
                            update_review( $textarea.val() );
                        }
                    });
                    
                },
                error: function() {
                    $error.text( gettext( "Oops... something went wrong :( Please accept our apologies." ) );
                    $error.fadeIn();
                    // ..
                    $ajax_loader.hide();
                }
            });
            return false;
        });
        return false;
    });

    // display wallposts
    var WALL_POSTER_HEIGHT = 82;
    var $posters = $( '.wall-posters:not(.bigger)', $wall );
    for( var i = 0; i < $posters.length; i++ ) {
        var p = $posters[i],
            $p = $( p );
        
        if ( p.scrollHeight > WALL_POSTER_HEIGHT ) {
            $( '<a class="show-more-posters" href="#">' + gettext( 'show all' ) + '</a>' )
                .click( function() {
                    var $this = $( this ),
                        $content = $this.prev(),
                        el = $content.get(0);
                    // ..
                    $this.remove();
                    $content.animate({
                         height: el.scrollHeight + 'px'
                    }, "slow" );
                    // ..
                    return false;
                }).insertAfter( $p );
        }
    };
};

FM.utils = {}

FM.utils.escape_html = function(text) {
    return $("<p>").text(text).html()
}

FM.utils.userprofile_url = function(username) {
    if(settings.SUBDOMAIN_AUTHORS)
        return "http://" + username + "." + settings.DOMAIN;
    else 
        return settings.FULL_DOMAIN + "/" + gettext("profile") + "/" + username;
}

FM.utils.replace_nicknames = function(text) {
    var nicks = text.match(/@[\w_-]+/g)
    console.log(nicks);
    for(var i=0; i<(nicks && nicks.length); i++) {
        var nick = nicks[i].substring(1);
        var url = "<a href='" + FM.utils.userprofile_url(nick) + "'>@" + nick + "</a>";
        text = text.replace(nicks[i], url);
    }
    return text;
}

FM.wallComments = function() {
    var $wall = $("#wall")
    ;
    
    // comment template factory
    function commentFactory(config) {
        var edit_comment = '',
            depth = config.depth || 0,
            resource_id = config.resource_uri.match(/([^\/]+)\/$/)[1];
        ;

        if(config.this_user_name === config.user_name) {
            edit_comment = '<a rel="' + config.resource_uri + '" class="edit-comment" href="#">' + gettext("Edit") + '</a>';
        }

        return ($('<section id="activity-' + resource_id + '" class="depth-' + depth + '"><header><p><a href="' + config.user_url + '">' + config.display_name +
                '<img width="45" height="45" alt="' + config.display_name + '" src="' + config.avatar_url + '" />' +
                '</a> </p></header><div class="c">' +
                config.comment +
                '</div><footer>' + edit_comment +
                ' <a rel="' + config.resource_uri + '" class="reply-comment" href="#">' + gettext("Reply") + '</a>' +
                '</footer></section>'));
    }

    if($wall.length > 0) {
        var $ajax_loader = $('<span class="ajax-loader"></span>'),
            page = 2
        ;

        // for each "leave comment" links, bind a form
        $wall.delegate(".comment", "click", function() {
            var $a = $(this),
                $form = $('<form class="cf"><textarea cols="40" rows="3"></textarea><button class="btn">OK</button><span class="ajax-loader"></span></form>'),
                $ajax_loader = $form.find(".ajax-loader"),
                $error = $('<p class="errorlist"></p>'),
                user_name = $("#display_name").attr("username"),
                $displayname = $("#display_name"),
                display_name = $displayname.text(),
                user_url = $displayname.attr("href"),
                post_comment_url = "http://" + location.host + "/api/" + FM.API_VERSION + "/comment/",
                get_avatar_url = "http://" + location.host + "/api/" + FM.API_VERSION + "/user/" + user_name + "/",
                object_uri = $(this).attr("rel"),
                get_comments_url = "http://" + location.host + "/api" + $(this).attr("rel") + "comments/?include=user,level&threaded=1&limit=999"
            ;

            // error handling
            $error.hide();
            $error.ajaxError(function() {
                var $this = $(this);
                $this.text(gettext("Oops... something went wrong :( Please accept our apologies."));
                $a.parents("footer").append($this);
                $this.show();
                $ajax_loader.hide();
                $a.removeClass("form-shown");
                $form.remove();
            });

            // submit comment
            $form.find("button").bind("click", function() {
                var comment = $form.find("textarea").val();
                if(comment === "") {
                    return false;
                }
                $ajax_loader.show();

                // submit post
                $.ajax({
                    type: "POST",
                    url: post_comment_url,
                    data: {
                        comment: comment,
                        object_uri: object_uri
                    },
                    success: function(msg) {
                        var post_process = function( html ) {
                            console.log( html );
                            console.log(msg);
                            // get user's avatar
                            $.ajax({
                                type: "GET",
                                url: get_avatar_url,
                                success: function(user) {
                                    console.log(user);
                                    var $new_comment/*,
                                        $leave_comment = $('<footer><p>' + gettext("0 min ago.") + ' <a rel="' + object_uri + '"href="http://' + location.host + object_uri + '" class="comment">' + gettext("Leave a comment") + '</a></p>')*/
                                    ;
                                    $new_comment = commentFactory({
                                            user_url: user_url,
                                            user_name: user_name,
                                            this_user_name: user_name,
                                            display_name: display_name,
                                            comment: html,
                                            resource_uri: msg.resource_uri,
                                            object_uri: object_uri,
                                            avatar_url: user.avatar.image_45
                                    });

                                    $new_comment.hide();

                                    $ajax_loader.hide();

                                    $a.removeClass("form-shown");

                                    // hide form, show new comment
                                    $form.slideUp("slow", function() {
                                        var $insertNode;
                                        //$a.parents("section").first().after($new_comment);
                                        if($a.parents("div").first().hasClass("wall-post")) {
                                            $a.parents("div").first().append($new_comment);
                                        } else
                                        if($a.parents("section").first().next("div.replies").length > 0) {
                                            $a.parents("section").first().next("div.replies").append($new_comment);
                                        } else {
                                            $a.parents("section").first().after('<div class="replies stream"></div>');
                                            $a.parents("section").first().next("div.replies").append($new_comment);
                                            //$a.parents("section").first().after($new_comment);
                                        }
                                        $form.remove();
                                        //$a.parents("section").first().append($a.parents("footer").first());
                                        $new_comment.slideDown("slow");
                        
                                        var resource_id = msg.resource_uri.match(/([^\/]+)\/$/)[1];
                                        $('html,body').animate({scrollTop: $("#activity-" + resource_id).offset().top - 20},'slow');
                                        $("#activity-" + resource_id).css({backgroundColor: "#ffffee"}).animate({backgroundColor: "transparent"}, 2000);
                                    });
                                }
                            });
                            
                            var $comment_count = $a.prev( ".has-comments" );
                            if( $comment_count.length == 0 ) {
                                $comment_count = $( '<a class="comment has-comments block" href="' + $a.attr( 'href' ) + '">0 comments</a>' ).insertBefore( $a );
                            }
                            var count = parseInt( $comment_count.text().match( /\d+/g )[0] ) + 1;
                            $comment_count.html( ' ' + count + ' ' + ngettext( 'comment', 'comments', count ) + ' ' );
                        
                            // remove delete link
                            $a.parent().find( ".remove-activity" ).remove();
                        };

                        // try fetch rendered comment ...
                        $.ajax({
                            type: 'GET',
                            url : '/ajax/render-comment/' + msg.resource_uri.match(/([^\/]+)\/$/)[1] + "/",
                            success: post_process,
                            error  : function( e ) {
                                console.log( 'error fetching rendered comment, need to set raw ... ', e );
                                post_process( FM.utils.replace_nicknames( FM.utils.escape_html( comment ) ) );
                            }
                        });
                    }
                });
                this.disabled = true;
                return false;
            }); // submit comment

            // show/hide form when appended to wall
            if($a.hasClass("form-shown")) {
                var $this_form = $a.parents("section").first().children(".cf");
                $this_form.slideUp("slow");
                $a.removeClass("form-shown").addClass("form-hidden");
                return false;
            } else if($a.hasClass("form-hidden")) {
                var $this_form = $a.parents("section").first().children(".cf");
                $a.removeClass("form-hidden").addClass("form-shown");
                $this_form.slideDown("slow");
                return false;
            }

            // load comments (if any)
            if($a.hasClass("has-comments")) {

                // check if the comments are already being loaded
                if($a.hasClass("block")) {
                    return false;
                }
                // prevent loading many times the same comments
                $a.addClass("block");

                $ajax_loader.css("display", "block");
                /*$a.parents("footer").append($ajax_loader);*/

                // load comments
                $.ajax({
                    type: "GET",
                    url: get_comments_url,
                    success: function(msg) {
                        var $tmp = $('<div class="replies stream"></div>');

                        for(var i = 0; i < msg.objects.length; i++) {
                            $tmp.append(
                            commentFactory({
                                user_url: FM.utils.userprofile_url(msg.objects[i].user.username),
                                this_user_name: user_name,
                                user_name: msg.objects[i].user.username,
                                display_name: msg.objects[i].user.display_name || msg.objects[i].user.username,
                                comment: msg.objects[i].comment,
                                object_uri: msg.objects[i].object_uri,
                                resource_uri: msg.objects[i].resource_uri,
                                avatar_url: msg.objects[i].user.avatar.image_45,
                                depth: msg.objects[i].level
                            }));
                        }

                        $ajax_loader.hide();

                        // append comments and form
                        if ($a.parents("section").first().next("div.replies").length > 0) {
                            $a.parents("section").first().next("div.replies").remove();
                        }
                        $a.parents("section").first().after($tmp.hide());
                        /*$tmp.append($a.parents("footer"));*/
                        if(user_name) {
                            $tmp.append($form.hide());
                            $form.find("textarea").autogrow();
/*                          $a.removeClass("has-comments").removeClass("block").addClass("form-hidden").text(gettext("Leave a comment"));*/
                        } else {
                            $a.remove();
                        }

                        $tmp.slideDown("slow");

                        // update comments publish time
                        jQuery( "time.timeago", $tmp ).timeago();
                    }
                });
                return false;
            } else {
                // append comment form
                $a.parents("section > footer").append($form);
                $form.find("textarea").autogrow();
                $form.hide().slideDown();
                $a.addClass("form-shown");
            }
            return false;
        }); // delegate click on a.comment


        // for each "edit" links, bind a form
        $wall.delegate(".edit-comment", "click", function() {
            var $a = $(this),
                $form = $('<form class="cf"><textarea cols="40" rows="3"></textarea><button class="btn">OK</button><span class="ajax-loader"></span></form>'),
                $ajax_loader = $form.find(".ajax-loader"),
                resource_uri = $a.attr("rel"),
                $p = $a.parents("footer").parent().find(".c"),
                comment = $p.text(),
                $textarea = $form.find("textarea")
            ;

            $form.hide();
            $form.insertAfter($p);

            $.getJSON( "http://" + location.host + "/api" + resource_uri, function( data ) {
                $textarea.val( data.comment );
                $p.slideUp("slow", function() {
                    $form.slideDown("slow");
                    $a.hide();
                });
            });

            $form.find("button").bind("click", function() {
                $ajax_loader.show();
                // submit post
                $.ajax({
                    type: "PUT",
                    url: "http://" + location.host + "/api" + resource_uri,
                    data: {
                        comment: $textarea.val()
                    },
                    success: function(msg) {

                        var post_process = function( html ) {
                            $ajax_loader.hide();
                            $p.html( html );
                            $form.slideUp("slow", function() {
                                $p.slideDown("slow");
                                $form.remove();
                                $a.show();
                            });
                        };

                        // try fetch rendered comment ...
                        $.ajax({
                            type: 'GET',
                            url : '/ajax/render-comment/' + resource_uri.match(/([^\/]+)\/$/)[1] + "/",
                            success: post_process,
                            error  : function( e ) {
                                console.log( 'error fetching rendered comment, need to set raw ... ', e );
                                post_process( FM.utils.replace_nicknames( FM.utils.escape_html( msg.comment ) ) );
                            }
                        });
                    }
                });
                return false;
            });
            return false;
        });

        // for each "reply" links, bind a form
        $wall.delegate(".reply-comment", "click", function() {
            var $a = $(this),
                $form = $('<form class="cf"><textarea cols="40" rows="3"></textarea><button class="btn">OK</button><span class="ajax-loader"></span></form>'),
                $this_form,
                $ajax_loader = $form.find(".ajax-loader"),
                $displayname = $("#display_name"),
                display_name = $displayname.text(),
                user_name = $displayname.attr("username"),
                user_url = $displayname.attr("href"),
                post_comment_url = "http://" + location.host + "/api/" + FM.API_VERSION + "/comment/",
                get_avatar_url = "http://" + location.host + "/api/" + FM.API_VERSION + "/user/" + user_name + "/",             parent_uri = $a.attr("rel"),
                parent_uri = $a.attr("rel"),
                object_uri = $a.parents('div.replies').first().prev('section').find('.comment').attr('rel');
                if(!object_uri)
                    object_uri = $('#wall').find('.comment').attr('rel') // detailed view case, for example article page

            // show/hide form when appended to wall
            if($a.hasClass("form-shown")) {
                $this_form = $a.parents("footer").first().nextAll(".cf");
                $this_form.slideUp("slow");
                $a.removeClass("form-shown").addClass("form-hidden");
                return false;
            } else if($a.hasClass("form-hidden")) {
                $this_form = $a.parents("footer").first().nextAll(".cf");
                $this_form.slideDown("slow");
                $a.removeClass("form-hidden").addClass("form-shown");
                return false;
            }
            
            $form.find("button").bind("click", function() {
                var comment = $form.find("textarea").val(),
                    depth = 0
                ;



                depth = $form.parent("section").attr("class");
                console.log(depth);
                depth = depth.slice(depth.indexOf("-") + 1, depth.length);
                depth++;

                console.log(depth);

                $ajax_loader.show();
                // submit post
                $.ajax({
                    type: "POST",
                    url: post_comment_url,
                    data: {
                        parent_uri: parent_uri,
                        object_uri: object_uri,
                        comment: comment
                    },
                    success: function(msg) {
                        var resource_uri = msg.resource_uri,
                            object_uri = msg.object_uri;
                        
                        var post_process = function( html ) {
                            // get user's avatar
                            $.ajax({
                                type: "GET",
                                url: get_avatar_url,
                                success: function(msg) {
                                    console.log(msg);
                                    var $new_comment,
                                        $leave_comment = $('<footer><p>0 mins ago. <a rel="' + object_uri + '"href="http://' + location.host + object_uri + '" class="comment">' + gettext("Reply") + '</a></p>')
                                    ;
                                    $new_comment = commentFactory({
                                            user_url: user_url,
                                            user_name: user_name,
                                            this_user_name: user_name,
                                            display_name: display_name,
                                            comment: html,
                                            depth: depth,
                                            resource_uri: resource_uri,
                                            object_uri: object_uri,
                                            avatar_url: msg.avatar.image_45
                                    });
                                    $new_comment.hide();
                                    $ajax_loader.hide();
                                    $a.removeClass("form-shown");
                                    // hide form, show new comment
                                    $form.slideUp("slow", function() {
                                        var $insertAfterThis;
                                        console.log("-------- " + $a.parents("section").first().next());
                                        if($a.parents("section").first().next("div.replies").length > 0) {
                                            $insertAfterThis = $a.parents("section").first().next("div.replies").first();
                                        } else {
                                            $insertAfterThis = $a.parents("section").first();
                                        }
                                        $insertAfterThis.after($new_comment);
                                        $form.remove();
                                        $new_comment.slideDown("slow");

                                        // update comment publish time
                                        jQuery( "time.timeago", $new_comment ).timeago();
                                    });
                                }
                            });
                        };

                        // try fetch rendered comment ...
                        $.ajax({
                            type: 'GET',
                            url : '/ajax/render-comment/' + resource_uri.match(/([^\/]+)\/$/)[1] + "/",
                            success: post_process,
                            error  : function( e ) {
                                console.log( 'error fetching rendered comment, need to set raw ... ', e );
                                post_process( FM.utils.replace_nicknames( FM.utils.escape_html( comment ) ) );
                            }
                        });
                    }
                });
                return false;
            });

            // append comment form
            $a.parents("section").first().append($form);
            $form.find("textarea").autogrow();
            $form.hide().slideDown();
            $a.addClass("form-shown");

            return false;
        });
        
        // remove activity
        $wall.delegate( ".remove-activity", "click", function() {
            var $this = $( this );
            $.confirmWindow({
                'id'         : uniqueId(),
                'title'      : gettext( 'Removing activity' ),
                'message'    : gettext( 'Do you want to remove this activity?' ),
                'successText': gettext( 'Remove activity' ),
                'onOk'       : function() {
                    this.disabled = true;
                    
                    $.ajax({
                        type   : 'POST',
                        url    : $this.attr( 'href' ),
                        success: function( msg ) {
                            $.closeTopLayer();
                            var $item = $this.closest( 'section' );
                            $item.animate( { opacity: 0. }, 1000, function() {
                                $item.slideUp( "slow" );
                            });
                        }
                    });
                    return false;
                }
            });
            return false;
        });

        // bind ajax fetcher
        $wall.delegate(".more a", "click", function() {
            var $more = $(this).parent('.more')
            $more.append($ajax_loader);
            // get all filters
            var filters_collection = $(".filters").find("a.selected"),
                filters = ""
            ;
            // create filter url segment if filters exist
            if(filters_collection.length > 0) {
                filters = "&" + $(filters_collection[0]).attr("href").slice(1);
            }
            $ajax_loader.show();
            $.ajax({
                type: 'GET',
                url: '?ajax' + filters + '&page=' + page,
                success: function(msg) {
                    $more.remove();
                    var tmp = $("<div></div>");
                    tmp.html(msg);
                    // if activities fetched
                    if($(tmp).find("section").length) {
                        var $msg = $( msg )

                        // update new wallposts publish time
                        jQuery( "time.timeago", $msg ).timeago();

                        // add new activities to DOM
                        $wall.append($msg);
                        page ++;

                    }
                }
            });
            return false; 
        });
        if($wall.hasClass("show-comment-form")) {
            $wall.find(".comment").not('.has-comments').click();
            // comments are already loaded ...
            $wall.find(".has-comments").addClass( 'block' );
        }
    }
}; // wallComments

FM.chooseCity = function() {
    var $id_city = $("#id_city");

    if($id_city.length > 0) {
        $id_city.bind("change", function() {
            $(this).parents("form").trigger("submit");
        });
    }
};

FM.confirmFormSubmits = function() {
    $('form.confirm').submit(function() {
        return confirm(gettext("Are you sure?"));
    });
};

FM.geo = {};

FM.geo.EARTH_R = 6367.449;

FM.geo.distance = function(p1, p2) {
    return 6371 * 2 * Math.asin(Math.sqrt(Math.pow(Math.sin((p1.lat() - Math.abs(p2.lat())) * Math.PI/180 / 2), 2) + Math.cos(p1.lat() * Math.PI/180 ) * Math.cos(Math.abs(p2.lat()) * Math.PI/180) * Math.pow(Math.sin((p1.lng()-p2.lng()) * Math.PI/180 / 2), 2)))
};


FM.geo.get_bounds = function(p, width) {
    var lat_delta = width / 2 * 1/(Math.PI / 180 * FM.geo.EARTH_R)
    var lng_delta = width / 2 * 1/(Math.PI / 180 * Math.cos(p.lat()*Math.PI/180) * FM.geo.EARTH_R)
    
//    if(p.lat()<0) lat_delta = -lat_delta;
//    if(p.lng()<0) lng_delta = -lng_delta;
    
    var sw = new google.maps.LatLng(p.lat() - lat_delta, p.lng() - lng_delta)
    var ne = new google.maps.LatLng(p.lat() + lat_delta, p.lng() + lng_delta)
    return new google.maps.LatLngBounds(sw, ne)
};

FM.geo.cities_around = function(pt, r, cb) {
        var bounds = FM.geo.get_bounds(pt, r);
        var ne = bounds.getNorthEast();
        var sw = bounds.getSouthWest();
        var n = ne.lat();
        var e = ne.lng();
        var s = sw.lat();
        var w = sw.lng();
        $.getJSON('http://api.geonames.org/citiesJSON?north='+n+'&south='+s+'&east='+e+'&west='+w+'&lang=en&username='+settings.GEONAMES_USERNAME+'&callback=?', cb)
};

FM.geo.timezone = function(pt, cb) {
    $.getJSON('http://api.geonames.org/timezoneJSON?lat='+pt.lat()+'&lng='+pt.lng()+'&username='+settings.GEONAMES_USERNAME+'&callback=?', cb)
};

FM.geo.getCurrentPosition = function(opts) {    
    function fetch_location() {
        navigator.geolocation.getCurrentPosition(function(pt) {
            $('#location_hint').hide();
            console.info(pt);
            opts.on_success(pt);
        }, function(err) {
            console.error(err);
            if(err.code == 1) {
                $('#location_err .msg').text(err.message);
                $('#location_err').show();
            }
        });
    }
    if(navigator.geolocation) {
        var cookies = document.cookie.split(';').map(function(s) {return $.trim(s)});
        if(opts.location_hint && cookies.indexOf('location_hint=0') < 0) {
            $('#location_hint .enable').click(function() {
                document.cookie='location_hint=0';
                fetch_location();
                return false;
            });
            $('#location_hint').show();
        } else {
            fetch_location();
        }
    }
};

FM.geo.locate = function() {
    if(settings.FULL_DOMAIN != document.location.origin) {
        return;
    }
    if(settings.IS_MOBILE && settings.IS_OAUTH)
        return
    FM.geo.getCurrentPosition({
        location_hint:false,
        on_success:function(pt) {
            document.cookie = "geolocation=" + encodeURIComponent(JSON.stringify(pt));
        }
    })
};

FM.follow = function() {
    var $follow_form = $("#followform")
    ;
    if($follow_form.length) {
        $follow_form.find("button").bind("click", function() {
            var $button = $follow_form.find("button"),
                $follow_val = $("#follow_val"),
                user_name = $("#display_name").attr("username"),
                followed_user = $("#follow-user-name").val(),
                follow_val = $follow_val.val(),
                $ajax_loader = $follow_form.find(".ajax-loader")
            ;

            $ajax_loader.show();

            if(follow_val == 1) {
                $.ajax({
                    type: 'POST',
                    url: "http://" + location.host + "/api/" + FM.API_VERSION + "/user/" + user_name + "/following/",
                    data: {
                        user_uri: "/" + FM.API_VERSION + "/user/" + followed_user + "/",
                        resource_uri: "/" + FM.API_VERSION + "/user/" + user_name + "/following/" + followed_user + "/"
                    },
                    success: function(msg) {
                        $follow_val.val(0);
                        $button.text(gettext("Unfollow"));
                        $ajax_loader.hide();
                    }
                });
            } else {
                $.ajax({
                    type: 'DELETE',
                    url: "http://" + location.host + "/api/" + FM.API_VERSION + "/user/" + user_name + "/following/" + followed_user + "/",
                    success: function(msg) {
                        $follow_val.val(1);
                        $button.text(gettext("Follow"));
                        $ajax_loader.hide();
                    }
                });
            }
            return false;
            
        });
    }
};

/**
 * updates number of rated movies on rate-movie page, checks recommendation status
 * @param config
 */
FM.rateMovieProgress = function(config) {
        $("body").bind("rated", function(event, type) {
            if((typeof type != "undefined") && (type != "1")) return;
            console.log("rated", type)
            var $progress_container = $("#rate-movies-progress"), t,
                status_check_delay = config.status_check_delay || 30000;
            var $movies_rated = $("#movies-rated"),
            $movies_to_rate = $("#movies-to-rate"),
            movies_rated = $movies_rated.text() || 0,
            movies_to_rate = $movies_to_rate.text() || 0,
            $rate_movie_progress = $("#rate-movie-progress"),
            $progress_info = $("#progress-info");

            if($movies_rated.length && $movies_to_rate.length && $rate_movie_progress.length) {
                if(movies_to_rate > 0) {
                    ++movies_rated;
                    --movies_to_rate;
                    $movies_rated.text(movies_rated);
                    $movies_to_rate.text(movies_to_rate);
                    $rate_movie_progress.css("width", (movies_rated * 100)/(movies_rated + movies_to_rate) + "%")
                }
                if(movies_to_rate < 1) {
                        //$progress_info.trigger("no_recommendations");
                    FM.reload_progress_widget(true)
                }
                /* dirty - expanding rating section on the mainpage */
                if($(".rate-movies-simple.collapsed")) {
                    $("body.home .rate-movies-simple.collapsed").animate({height: '460px'}, "slow", function() {$(this).removeClass("collapsed");});
                }
            }
        });

};

FM.reload_progress_widget = function(force) {
    function check_autoreload() {
        if(FM._progress_reload_tid)
            clearTimeout(FM._progress_reload_tid)
        var reload_delay = $("#rate-movies-progress").attr('data-reload-delay')
        if(reload_delay) {
            FM._progress_reload_tid = setInterval(reload, reload_delay);
        }
    }

    function reload() {
        var pc = $(".global-progress")
        var tmp = $('<div>').load('/ajax/widget/badges/user_progress/', function(msg, status, xhr) {
            if(msg && status!='error' && $(this).find('#progress-info').attr('data-goal-state') != pc.find('#progress-info').attr('data-goal-state')) {
                pc.replaceWith(tmp.find('> *'))
                FM.fixMarkup($(".global-progress"));
                var info = $('#progress-info')
                info.css("background-color", "#ff0")
                            .stop()
                            .animate({
                                backgroundColor: "#191919"
                            }, 1000)
                check_autoreload()
            }
        })
    }

    if(force) reload();

    check_autoreload()
}

FM.ajaxizeSignupForm = function (scope) {
    scope = scope || $('body')
    var ajax_signup = scope.find('#ajax-signup')
    var o = ajax_signup.find('form.ajax').ajaxForm({
        beforeSubmit: function() {
            $('#ajax-signup .ajax-loader').show()
            return true;
        },
        success: function(msg, status, xhr) {
            if(msg.status == 'ok') {
                window.location.assign(msg.next || '/');
                return;
            }
            ajax_signup.replaceWith(msg)
            $('#ajax-signup').show()
            FM.ajaxizeSignupForm($('body'));
            FM.set_iframe_height()
        }
    })
}
/**
 * check recommendation status
 */
FM.checkRecommendationStatus = function() {
    var $progress_info = $("#progress-info")
    ;
    if($progress_info.length) {
        $.ajax({
            type: "GET",
            url: "http://" + location.host + "/ajax/recommendations-status/",
            success: function(msg) {
                if(msg.recommendations_status === 2) {
                    $progress_info.trigger("no_recommendations");
                } else if(msg.recommendations_status === 3) {
                    $progress_info.trigger("quick_recommendations");
                } else if(msg.recommendations_status === 1) {
                    $progress_info.trigger("full_recommendations");
                }
            }
        });
    }
};

/**
 * updates rate movie progress info
 */
FM.progressInfo = function() {
    var $progress_info = $("#progress-info")
    ;
    function showInfo(html, event_name) {
        if(!$progress_info.hasClass(event_name)) {
            $progress_info.html(html)
                            .css("background-color", "#ff0")
                            .stop()
                            .animate({
                                backgroundColor: "#191919"
                            }, 1000)
                            .addClass(event_name);
            //$('html,body').animate({
            //  scrollTop: $progress_info.offset().top
            //}, 500);
        }
    }
    if($progress_info.length) {
        var recommendations_url = $(".m_r a").attr("href")
        ;
        // no recommendations are ready yet
        $progress_info.bind("no_recommendations", function(e) {
            showInfo(gettext("Your recommendations are getting computed right now. They should be ready in a few seconds"),
                    e.type);
        });

        // quick recommendations
        $progress_info.bind("quick_recommendations", function(e) {
            showInfo(gettext("We've prepared personalized movie recommendations for you") +
                    " - " + '<a href="' + recommendations_url + '">' +
                    gettext("check them out!") + '</a>',
                    e.type);
        });

        // full recommendations
        $progress_info.bind("full_recommendations", function(e) {
            showInfo(gettext("We've prepared personalized movie recommendations for you") +
                    " - " + '<a href="' + recommendations_url + '">' +
                    gettext("check them out!") + '</a>',
                    e.type);
        });
    }
};

/**
 * loads new set of movie rating widgets
 */
FM.rateMovieLoader = function() {
    var $rate_movies_more = $(".rate-movies-more").find(".button, .main-button")
    ;
    
    if($rate_movies_more.length) {
        var $widgets_list = $("ul.rate-movies-simple"),
            $wrapper,
            $ajax_loader = $rate_movies_more.next()
        ;
        $widgets_list.wrap('<div class="wrapper"></div>');
        $wrapper = $("#main").find(".wrapper");

        $rate_movies_more.bind("click", function() {
            $ajax_loader.css("display", "block");
            $widgets_list = $wrapper.children(".rate-movies-simple");
            $widgets_list.css("opacity", "1")
                    .stop()
                    .animate({opacity: 0.3}, 2000);
            $wrapper.addClass("loading");
            var url = $rate_movies_more.attr("href");
            $.ajax({
                type: "POST",
                url: url + (url.indexOf('?')<0 ? '?' : '&') + "ajax",
                data: {prev_film_ids: FM._prev_film_ids()},
                success: function(msg) {
                    //console.log(msg);
                    $ajax_loader.hide();
                    $wrapper.removeClass("loading");
                    $wrapper.html(msg).css("opacity", "0.3")
                            .stop()
                            .animate({opacity: 1}, 2000);
                    $wrapper.find(".rate-movie").each(function() {
                        FM.rateMovieWidgetSmall({widget: $(this)});
                    });
                }
            });
            return false;
        });
    }
};

FM.loadAjaxWidgets = function() {
    $('.ajax-widget').each(function(i) {
        var w = $(this);
        var url = w.attr('data-url');
        $.get(url, null, function(data) {
            var tmp = $('<div>')
            tmp[0].innerHTML = data;
            FM.fixMarkup(tmp);
            w.replaceWith(tmp.children());
    
        })
    })
}

FM.filmCheckinButton = function(scope) {
    function update_label(button) {
        var rel = button.attr('rel');
        var film_uri = button.attr('data-film-uri')
        var txt = rel && gettext("Cancel") || film_uri && gettext("I'm watching now") || gettext("I'm going to watch");
        button.text(txt)
    }
    scope.find('section.checkin').each(function() {
        var $widget=$(this);
        var button = $widget.find('button')
        button.click(function() {
            var ajax_loader = $widget.find('.ajax-loader').show()
            var rel = button.attr('rel');
            var film_uri = button.attr('data-film-uri')
            var screening_uri = button.attr('data-screening-uri')
            if(rel) {
                $.ajax({
                    url:'/api' + rel,
                    type:'DELETE',
                    success:function(data) {
                        button.attr('rel', '');
                        update_label(button);
                        ajax_loader.hide();
                    }
                })
            } else {
                var data = {}
                if(film_uri) {
                    data['film_uri'] = film_uri
                } else {
                    data['screening_uri'] = screening_uri
                }
                $.ajax({
                    url:'/api/' + FM.API_VERSION + '/checkin/', 
                    type:'POST', 
                    data:data, 
                    success:function(data){
                        button.attr('rel', data.resource_uri)
                        update_label(button);
                        ajax_loader.hide();
                    }
                })
            }
        })
        update_label(button);
        $('<span class="ajax-loader"></span>').insertAfter(button);
    })
}

FM.ajaxPrefilter = function() {
    $.ajaxPrefilter(function(settings) {
        if(settings.type == 'DELETE') {
            settings.type = 'POST';
            settings.data = 'method=DELETE';
        }
    });
}

FM.watching_form = function() {
    var form = $('#watching_form')
    var loader = form.find('.ajax-loader')
    $('#watching_form input[type=submit]').hide();
    $('#id_is_observed').change(function() {
        loader.show();
        form.ajaxSubmit({
            success: function() {
                loader.hide();
            }
        });
    });
}
FM.ajaxSignup = function() {
    $('body').delegate('a.ajax-signup', 'click', function() {
        document.cookie = "ajax_signup=1; expires=Sat, 01 Dec 2022 00:00:00 UTC; path=/; domain=" + settings.DOMAIN.split(':')[0];
        var reg_url = $('iframe.ajax-signup').attr('rel')
        $('iframe.ajax-signup').css('height', '0').show().attr('src', (settings.FORCE_SSL_LOGIN ? 'https://' : 'http://') + settings.DOMAIN + reg_url + '?iframe');
        return false;
    });
}
FM.showAjaxSignup = function(scope) {
    if(document.cookie.indexOf('ajax_signup=1')<0) {
        scope = scope || $('body');
        scope.find('a.ajax-signup').click()
    }
}

FM.initRaterWidget = function() {
    var films = $('.rate-movies-simple .rate-movie')
    if(!films.length)
        $('.rate-movies-more a:first').click()
}
FM.set_iframe_height = function() {
        var h = $('body').height();
        if(h != window._body_height) {
            window._body_height = h;
            parent.postMessage('set_iframe_height('+ document.location.href + ',' + h + ')', '*');
            console.log(h);
        }
}
FM.iframe_auto_height = function() {
    window.addEventListener('message', function(event) {
            var m = /set_iframe_height\((.*)\,(\d+)\)/.exec(event.data);
            if(m) {
                var frames = $('iframe')
                for(var i=0; i<frames.length; i++) {
                    if(frames[i].src == m[1]) {
                        $(frames[i]).css('height', m[2] + 'px');
                    }
                }
            }
    });
}
/* ----------------------------------- init ----------------------------------- */

window.fb_init && fb_init();

FM.rateMovieWidget({
});

FM.rateMovieWidgetSmall({
});

FM.rateMovieWidgetSimple({
});
FM.ratingWidget({});

FM.chooseCity();

FM.wallComments();

FM.wallPost();

FM.flashMessages({
});

FM.confirmFormSubmits({
});

FM.follow();

FM.watching_form();

if(!window.disable_geolocation)
    FM.geo.locate();

FM.rateMovieProgress({
    status_check_delay: 5000
});

FM.reload_progress_widget()
//FM.ajaxizeSignupForm()

FM.progressInfo();
FM.loadAjaxWidgets();
FM.rateMovieLoader();
FM.ajaxPrefilter();
FM.ajaxSignup();
FM.showAjaxSignup();

$("form.register").preventDoubleSubmit();

// update publish time
jQuery( "time.timeago" ).timeago();

FM.ratingAjax = $.manageAjax.create('rating', {
    queue: true,
    preventDoubleRequests: false,
});
FM.rateNextAjax = $.manageAjax.create('ratenext', {
    queue: true,
    preventDoubleRequests: false,
});

FM.initRaterWidget();
FM.postInit();
FM.iframe_auto_height();

