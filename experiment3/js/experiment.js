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
  {
    "clozeTests": [
      {"chainID": "102", "clozeIndex": 5},
      {"chainID": "102", "clozeIndex": 7},
      {"chainID": "62", "clozeIndex": 0}
    ],
    "docIndex": "151"
  },
  {
    "clozeTests": [
      {"chainID": "41", "clozeIndex": 2},
      {"chainID": "41", "clozeIndex": 0},
      {"chainID": "125", "clozeIndex": 1}
    ],
    "docIndex": "120"
  },
  {
    "clozeTests": [
      {"chainID": "84", "clozeIndex": 0}, 
      {"chainID": "84", "clozeIndex": 1}
    ],
    "docIndex": "063"
  },
  {
    "clozeTests": [
      {"chainID": "41", "clozeIndex": 0}, 
      {"chainID": "41", "clozeIndex": 1}, 
      {"chainID": "21", "clozeIndex": 0}
    ],
    "docIndex": "243"
  },
  {
    "clozeTests": [
      {"chainID": "68", "clozeIndex": 3},
      {"chainID": "68", "clozeIndex": 5},
      {"chainID": "68", "clozeIndex": 6}
    ],
    "docIndex": "196"
  },
  {
    "clozeTests": [
      {"chainID": "11", "clozeIndex": 4},
      {"chainID": "11", "clozeIndex": 3},
      {"chainID": "133", "clozeIndex": 0}
    ], "docIndex": "191"
  },
  {
    "clozeTests": [
      {"chainID": "40", "clozeIndex": 0},
      {"chainID": "40", "clozeIndex": 1}
    ],
    "docIndex": "086"
  },
  {
    "clozeTests": [
      {"chainID": "10", "clozeIndex": 1},
      {"chainID": "10", "clozeIndex": 0},
      {"chainID": "47", "clozeIndex": 1}
    ],
    "docIndex": "025"
  },
  {
    "clozeTests": [
      {"chainID": "18", "clozeIndex": 0},
      {"chainID": "18", "clozeIndex": 1},
      {"chainID": "18", "clozeIndex": 2}
    ],
    "docIndex": "271"
  },
  {
    "clozeTests": [
      {"chainID": "29", "clozeIndex": 0},
      {"chainID": "29", "clozeIndex": 1},
      {"chainID": "58", "clozeIndex": 0}
    ],
    "docIndex": "171"
  },
  {
    "clozeTests": [
      {"chainID": "88", "clozeIndex": 1},
      {"chainID": "88", "clozeIndex": 4},
      {"chainID": "88", "clozeIndex": 5}
    ],
    "docIndex": "023"
  },
  {
    "clozeTests": [
      {"chainID": "78", "clozeIndex": 1},
      {"chainID": "78", "clozeIndex": 0},
      {"chainID": "48", "clozeIndex": 1}
    ],
    "docIndex": "022"
  },
  {
    "clozeTests": [
      {"chainID": "168", "clozeIndex": 2},
      {"chainID": "168", "clozeIndex": 0},
      {"chainID": "20", "clozeIndex": 1}
    ],
    "docIndex": "177"
  },
  {
    "clozeTests": [
      {"chainID": "76", "clozeIndex": 0},
      {"chainID": "76", "clozeIndex": 1}
    ],
    "docIndex": "033"
  },
  {
    "clozeTests": [
      {"chainID": "110", "clozeIndex": 1},
      {"chainID": "110", "clozeIndex": 3},
      {"chainID": "110", "clozeIndex": 2}
    ],
    "docIndex": "050"
  },
  {
    "clozeTests": [
      {"chainID": "86", "clozeIndex": 0},
      {"chainID": "86", "clozeIndex": 1}
    ],
    "docIndex": "248"},
  {
    "clozeTests": [
      {"chainID": "22", "clozeIndex": 0},
      {"chainID": "22", "clozeIndex": 1}
    ],
    "docIndex": "153"}];

var myTrials = [];
for (var i=0; i<clozeData.length; i++) {
  var clozeDatum = clozeData[i];
  var doc = clozeDatum["docIndex"]; //documents are unique across "clozeData" elements
  var clozeTests = clozeDatum.clozeTests; //multiple cloze tests exist per document. we will sample from these.
  var clozeTest = _.sample(clozeTests);
  // for (var j=0; j<clozeTests.length; j++) {
    // var clozeTest = clozeTests[j]
    var chain = clozeTest.chainID;
    var cloze = clozeTest.clozeIndex;
    myTrials.push({
      'document': doc,
      'chain': chain,
      'cloze': cloze
    })
  // } 
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
  totalNQns: clozeData.length + 3,
  /*intro, demographic, debriefing*/
  // log data to send to mturk here
  data: {
    trials: [],
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
    if (logSuccess == 'CHECK_RESPONSE') {
      $(".submit").hide();
      $(".parsing").show();
      // give Ss some indication that something will happen.
      setTimeout(function() {
        $(".submit").show();
        $(".parsing").hide();
        logSuccess = (experiment.state.parser_response == 'GOOD_RESPONSE' |
          experiment.state.parser_response == 'NO_RESPONSE_FROM_PARSER')
        if (experiment.state.parser_response == 'NO_RESPONSE_FROM_PARSER') {
          var chain = experiment.state.chain;
          var clozeIndex = chain.cloze;
          var condition = experiment.data.condition;
          experiment.data.trials.push({
                  document: chain.document,
                  chain: chain.chain,
                  condition: condition,
                  response: response,
                  original: $(".story." + condition +
                    ".document" + chain.document +
                    ".chain" + chain.chain +
                    ">.story_segment.clozeIndex" + clozeIndex +
                    ".blurry").text(),
                  gloss: $(".story." + condition +
                    ".document" + chain.document +
                    ".chain" + chain.chain +
                    ">.story_segment.clozeIndex" + clozeIndex +
                    ".gloss").text(),
                  clozeIndex: clozeIndex,
                  storyHTML: $(".story." + condition +
                    ".document" + chain.document +
                    ".chain" + chain.chain).html(),
                  trialnum: experiment.state.trialnum,
                  rt: trialResponseTime - trialStartTime
          })
        }
        if (logSuccess) {
          experiment.state.trialnum++;
          experiment.progress();
          var state = experimentStates.shift();
          experiment[state]();
        } else {
          experiment.state.responseError();
        }
      }, 2000);
    } else {
      if (logSuccess) {
        experiment.state.trialnum++;
        experiment.progress();
        var state = experimentStates.shift();
        experiment[state]();
      } else {
        experiment.state.responseError();
      }
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
    $(".startbutton").click(function() {
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
    $(".submit").show();
    $(".parsing").hide();
    var trialStartTime = time();
    $('.response').remove();
    $('.prompt').remove();
    showSlide("trial");
    if (experiment.data.condition=="original") {
      $(".instructions.caveman").hide();
    } else {
      $(".instructions.full_text").hide();
    }
    var chain = myTrials.shift();
    experiment.state.chain = chain;
    var clozeIndex = chain.cloze;
    var condition = experiment.data.condition;
    $(".story").hide();
    $(".story." + condition +
      ".document" + chain.document +
      ".chain" + chain.chain).show();
    $(".story." + condition +
      ".document" + chain.document +
      ".chain" + chain.chain + ">.story_segment").show();
    var clozeTestOriginalID = ".story." + condition +
      ".document" + chain.document +
      ".chain" + chain.chain +
      ">.story_segment.clozeIndex" + clozeIndex;
    $(clozeTestOriginalID).hide();

    var responseInput = "<p class='story_segment prompt'>" +
      "Please guess the sentence that was here:</p>\n" +
      "<input class='story_segment response'></input>"
    $(clozeTestOriginalID).before(responseInput);

    // var responseInput = $('<input/>', {type: 'text', class: 'response', size: '40'});
    experiment.state.log = function() {
      var trialResponseTime = time();
      var response = $('.response').val();
      experiment.state.parser_response = 'NO_RESPONSE_FROM_PARSER'
      if (response.length == 0) {
        experiment.state.parser_response = 'NO_TEXT'
      } else {
        $.post( '//erindb.me/cgi-bin/nlp.py', {'text': response, 'annotators': 'parse'})
          .done(function(data) {
            // console.log('i posted and stuff happened.');
            // console.log('the response: ' + data);
            // console.log(data)
            data = JSON.parse(data);
            if (data.sentences.length == 0) {
              experiment.state.parser_response = 'NO_TEXT'
            } else {
              exactlyOneSentence = data.sentences.length == 1;
              firstIsSentence = data.sentences[0].parse[9]=='S';
              if (firstIsSentence & exactlyOneSentence) {
                experiment.data.trials.push({
                  document: chain.document,
                  chain: chain.chain,
                  condition: condition,
                  response: response,
                  original: $(".document" + chain.document +
                    "." + experiment.data.condition +
                    ".chain" + chain.chain +
                    ">.story_segment.sentence.clozeIndex" + clozeIndex +
                    ">.blurry").text(),
                  gloss: $(".document" + chain.document +
                    "." + experiment.data.condition +
                    ".chain" + chain.chain +
                    ">.story_segment.sentence.clozeIndex" + clozeIndex +
                    ">.gloss").text(),
                  clozeIndex: clozeIndex,
                  storyHTML: $(".story." + condition +
                    "." + experiment.data.condition +
                    ".document" + chain.document +
                    ".chain" + chain.chain).html(),
                  trialnum: experiment.state.trialnum,
                  rt: trialResponseTime - trialStartTime
                })
                experiment.state.parser_response = 'GOOD_RESPONSE'
              } else {
                experiment.state.parser_response = 'MULTIPLE_SENTENCES'
              }
            }
          });
        // console.log('i tried to post. and the code is still running.');
      }
      return 'CHECK_RESPONSE'
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
    // clearInterval(mouseLoggerId);
    experiment.data.startTime = startTime;
    experiment.data.seed =  aRandomSeed;
    // Show the finish slide.
    showSlide("finished");
    // Wait 1.5 seconds and then submit the whole experiment object to Mechanical Turk (mmturkey filters out the functions so we know we're just submitting properties [i.e. data])
    setTimeout(function() { turk.submit(experiment.data) }, 1500);
    // console.log(JSON.stringify(experiment.data));
  },
  debriefing: function() {
    showSlide("debriefing");
  }
};

// -------- run experiment ----------
var experimentStates = ["intro"].concat(
      _.shuffle(rep("trial", clozeData.length))
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
  
  experiment.data.condition = _.sample(['caveman', 'original', 'event_only']);

  var repeatWorker = false;
  if (repeatWorker) {
    $('.slide').empty();
    alert("You have already completed the maximum number of HITs allowed by this requester. Please click 'Return HIT'.");
  }
})