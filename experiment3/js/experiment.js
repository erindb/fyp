// -------- helper functions & utilities ----------
String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}
function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min)) + min;
}
function rep(obj, n) {
  return new Array(n).fill(obj);
}
var startTime = (new Date()).getTime();
function time() {
  var now = (new Date()).getTime();
  return now - startTime;
}

var clozeData = [
  {"clozeTests": [{"chainID": "62", "clozeIndex": 0}, {"chainID": "62", "clozeIndex": 1}, {"chainID": "61", "clozeIndex": 1}], "docIndex": "151"}, 
  {"clozeTests": [{"chainID": "125", "clozeIndex": 2}, {"chainID": "125", "clozeIndex": 3}, {"chainID": "41", "clozeIndex": 2}], "docIndex": "120"}, 
  {"clozeTests": [{"chainID": "84", "clozeIndex": 0}, {"chainID": "84", "clozeIndex": 1}], "docIndex": "063"}, 
  {"clozeTests": [{"chainID": "41", "clozeIndex": 1}, {"chainID": "41", "clozeIndex": 0}, {"chainID": "21", "clozeIndex": 0}], "docIndex": "243"}, 
  {"clozeTests": [{"chainID": "68", "clozeIndex": 6}, {"chainID": "68", "clozeIndex": 1}, {"chainID": "68", "clozeIndex": 2}], "docIndex": "196"}, 
  {"clozeTests": [{"chainID": "11", "clozeIndex": 4}, {"chainID": "11", "clozeIndex": 3}, {"chainID": "133", "clozeIndex": 1}], "docIndex": "191"}, 
  {"clozeTests": [{"chainID": "40", "clozeIndex": 0}, {"chainID": "40", "clozeIndex": 1}], "docIndex": "086"}, 
  {"clozeTests": [{"chainID": "58", "clozeIndex": 5}, {"chainID": "58", "clozeIndex": 4}, {"chainID": "10", "clozeIndex": 1}], "docIndex": "025"}, 
  {"clozeTests": [{"chainID": "18", "clozeIndex": 0}, {"chainID": "18", "clozeIndex": 1}, {"chainID": "18", "clozeIndex": 2}], "docIndex": "271"}, 
  {"clozeTests": [{"chainID": "58", "clozeIndex": 1}, {"chainID": "58", "clozeIndex": 0}, {"chainID": "29", "clozeIndex": 1}], "docIndex": "171"}, 
  {"clozeTests": [{"chainID": "88", "clozeIndex": 3}, {"chainID": "88", "clozeIndex": 6}, {"chainID": "88", "clozeIndex": 5}], "docIndex": "023"}, 
  {"clozeTests": [{"chainID": "78", "clozeIndex": 0}, {"chainID": "78", "clozeIndex": 1}, {"chainID": "48", "clozeIndex": 0}], "docIndex": "022"}, 
  {"clozeTests": [{"chainID": "177", "clozeIndex": 0}, {"chainID": "177", "clozeIndex": 1}, {"chainID": "20", "clozeIndex": 1}], "docIndex": "177"}, 
  {"clozeTests": [{"chainID": "76", "clozeIndex": 0}, {"chainID": "76", "clozeIndex": 1}], "docIndex": "033"}, 
  {"clozeTests": [{"chainID": "110", "clozeIndex": 0}, {"chainID": "110", "clozeIndex": 2}, {"chainID": "110", "clozeIndex": 3}], "docIndex": "050"}, 
  {"clozeTests": [{"chainID": "86", "clozeIndex": 0}, {"chainID": "86", "clozeIndex": 1}], "docIndex": "248"}, 
  {"clozeTests": [{"chainID": "22", "clozeIndex": 0}, {"chainID": "22", "clozeIndex": 1}], "docIndex": "153"}
]

var myTrials = [];
for (var i=0; i<clozeData.length; i++) {
  var clozeDatum = clozeData[i];
  var doc = clozeDatum["document"];
  var clozeTests = clozeDatum.clozeTests;
  for (var j=0; j<clozeTests.length; j++) {
    var clozeTest = clozeTests[j]
    var chain = clozeTest[0];
    var cloze = clozeTest[1];
    myTrials.push({
      'document': doc,
      'chain': chain,
      'cloze': cloze
    })
  } 
};
myTrials = _.shuffle(myTrials);

// Shows slides. We're using jQuery here - the **$** is the jQuery selector function, which takes as input either a DOM element or a CSS selector string.
function showSlide(id) {
  // Hide all slides
  $(".slide").hide();
  // Show just the slide we want to show
  $("#"+id).show();
}

$(".slide").append('<div class="progress"><span>Progress: </span>' +
    '<div class="bar-wrapper"><div class="bar" width="0%">' +
    '</div></div></div>')

// -------- experiment structure ----------
var experiment = {
  totalNQns: 10 + 4 + 1, /*intro, instructions, demographic, debriefing, attention*/
  // log data to send to mturk here
  data: {
    trials: [],
    events: [],
    demographics: [],
    randomSeed: aRandomSeed,
  },
  // store state information here
  state: {
    trialnum: -1,
    next: function() { return experiment.defaultNext() },
    log: function() { return experiment.defaultLog() },
    responseError: function() { return experiment.defaultResponseError() },
  },
  defaultLog: function() {
    return true;
  },
  defaultNext: function() {
    var logSuccess = experiment.state.log();
    if (logSuccess) {
      experiment.state.trialnum++;
      experiment.progress();
      var state = experimentStates.shift();
      experiment[state]();
    } else {
      experiment.state.responseError();
    }
  },
  defaultResponseError: function() {
    $('.err').show();
  },
  progress: function() {
    $('.err').hide();
    var nQns = experiment.state.trialnum;
    $('.bar').css('width', ( (nQns / experiment.totalNQns)*100 + "%"));
  },
  intro: function() {
    showSlide("intro");
    $(".start").click(function() {
      $(this).unbind("click");
      experiment.state.next();
    })
  },
  // first slide (instructions)
  instructions: function() {
    showSlide("instructions");
  },
  // run at start of block
  trial: function() {
    var trialStartTime = time();
    $('.response').remove();
    $('#continue').remove();
    showSlide("trial");
    var chain = myTrials.shift();
    console.log(chain);
    // var nCloze = $('.document' + trialData.document + '.chain' + trialData.chain + '.cloze').length;
    var clozeIndex = chain.cloze;
    var condition = experiment.data.condition;
    var clozeSpans = $('.' + condition + '.cloze.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex);
    if (clozeSpans.length == 0) {
      clozeIndex = clozeIndex - 1;
    }
    $('.chain').hide();


    $('.' + condition + '.chain.document' + chain.document + '.chain' + chain.chain).show();
    $('.' + condition + '.cloze.document' + chain.document + '.chain' + chain.chain).show();
    $('.' + condition + '.cloze.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).hide();
    // var responseInput = $('<input/>', {type: 'text', class: 'response', size: '40'});
    var responseInput = "<p class='story_segment prompt'>Please guess the sentence that was here:</p>\n<input class='story_segment response'></input>"
    $('.' + condition + '.cloze.blurry.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).hide();
    $('.' + condition + '.cloze.gloss.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).before(responseInput);
    experiment.state.log = function() {
      var trialResponseTime = time();
      var response = $('.response').val();
      if (response.length > 0) {
        experiment.data.trials.push({
          document: chain.document,
          chain: chain.chain,
          condition: condition,
          response: response,
          full: $('.full.cloze.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).text(),
          caveman: $('.caveman.cloze.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).text(),
          event: $('.event.cloze.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).text(),
          original: $('.' + condition + '.cloze.document' + chain.document + '.chain' + chain.chain + '.cloze' + clozeIndex).text(),
          clozeIndex: clozeIndex,
          clozeHTML: $('.' + condition + '.chain.document' + chain.document + '.chain' + chain.chain).html(),
          clozeText: $('.' + condition + '.chain.document' + chain.document + '.chain' + chain.chain).text(),
          trialnum: experiment.state.trialnum,
          rt: trialResponseTime - trialStartTime
        })
        return true;
      } else {
        return false;
      }
    }
  },
  attention: function() {
    var trialStartTime = time();
    showSlide("attention");
    experiment.state.log = function() {
      var trialResponseTime = time();
      var response = $('.attentionResponse').val();
      if (response.length > 0) {
        experiment.data.trials.push({
          document: 'attention',
          chain: 'attention',
          response: response,
          original: 'apples',
          clozeIndex: 'attention',
          clozeHTML: $('.attention').html(),
          trialnum: experiment.state.trialnum,
          rt: trialResponseTime - trialStartTime
        })
        return true;
      } else {
        return false;
      }
    }
  },
  demographic: function() {
    $(".languageFree").hide();
    showSlide("demographic");
    $("#language").change(function() {
      if ($("#language").val() == 'eng+other' | $("#language").val() == 'other') {
        $(".languageFree").show();
      } else {
        $(".languageFree").hide();
      }
    })
    experiment.state.log = function() {
      var language = $("#language").val();
      var languageFree = $("#languageFree").val();
      var gender = $("#gender").val();
      var age = $("#age").val();
      var ethnicity = $("#ethnicity").val();
      var education = $("#education").val();
      var studyQuestionGuess = $("#studyQuestionGuess").val();
      var comments = $("#comments").val();
      if (language=='' | gender=='' | education=='') {
        // if blanks, no successful log
        return false;
      } else {
        var demographics = [
          'language', 'languageFree', 'gender', 'age',
          'ethnicity', 'education', 'studyQuestionGuess', 'comments'
        ];
        for (var i=0; i<demographics.length; i++) {
          var demographic = demographics[i];
          experiment.data.demographics.push({
            response: $("#" + demographic).val(),
            qtype: demographic
          })
        }
        return true;
      }
    }
    experiment.state.responseError = function() {
      $(".footnote").css({color: "red"});
      $("#language").click(function() {
        $(".footnote").css({color: "black"});
      })
      $("#gender").click(function() {
        $(".footnote").css({color: "black"});
      })
      $("#education").click(function() {
        $(".footnote").css({color: "black"});
      })
    }
  },
  finished: function() {
    experiment.state.log = experiment.defaultLog();
    clearInterval(mouseLoggerId);
    experiment.data.startTime = startTime;
    experiment.data.seed =  aRandomSeed;
    // Show the finish slide.
    showSlide("finished");
    // Wait 1.5 seconds and then submit the whole experiment object to Mechanical Turk (mmturkey filters out the functions so we know we're just submitting properties [i.e. data])
    setTimeout(function() { turk.submit(experiment.data) }, 1500);
    console.log(JSON.stringify(experiment.data));
  },
  debriefing: function() {
    showSlide("debriefing");
  }
};

// -------- run experiment ----------
var experimentStates = ["intro"].concat(
      _.shuffle(rep("trial", 10).concat(['attention']))
    ).concat(["demographic", "debriefing", "finished"]);

$(document).ready(function() {

  // $('.slide').hide(); //hide everything
  $('#intro').show();

  //make sure turkers have accepted HIT (or you're not in mturk)
  if (turk.previewMode) {
    $("#mustaccept").show();
  } else {
    experiment.state.next();
  }
  
  experiment.data.condition = _.sample(['caveman', 'full', 'event']);

  var repeatWorker = false;
  if (repeatWorker) {
    $('.slide').empty();
    alert("You have already completed the maximum number of HITs allowed by this requester. Please click 'Return HIT'.");
  }
})

// -------- record all the events ----------
var x = 0;
var y = 0;

var slideLeftMargin = parseFloat($(".slide").css("margin-left")) +
      parseFloat($(".slide").css("padding-left"))

document.onmousemove = function(e) {
  x = (e.pageX - slideLeftMargin) / $(".slide").width();
  y = e.pageY / $(".slide").height();
};
$(document).click(function(e) {
  experiment.data.events.push({
        type: "click",
        x: x,
        y: y,
        time: time()
  });
});
$(document).keyup(function(e){
  experiment.data.events.push({
        type: "keyup",
        keyCode: e.keyCode,
        key: String.fromCharCode(e.keyCode),
        time: time()
  });
});
var mouseLoggerId;
$(document).ready(function() {
  $(".continue").click(function() {
    $(this).unbind("click");
    this.blur();
    experiment.data.events.push({
          type: "click",
          x: x,
          y: y,
          time: time()
    });
    experiment.next();
  });
  mouseLoggerId = setInterval(function(e) {
    experiment.data.events.push({
          type: "position",
          x: x,
          y: y,
          time: time()
    });
  }, 50);
});