/*
 * Copyright (C) 2010 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function () {

/* ------------- *
 * --- Utils --- *
 * ------------- */

var blogspotty = {};
window.blogspotty = blogspotty;

Array.prototype.isArray = function () { return true; };
Object.prototype.isArray = function () { return false; };
String.prototype.isString = function () { return true; };
Object.prototype.isString = function () { return false; };

Element.prototype.addClassName = function (name) {
  var parts = this.className.split(" ");
  for (var i = 0; i < parts.length; i++) {
    if (parts[i] == name)
      return;
  }
  parts.push(name);
  this.className = parts.join(" ");
};

Element.prototype.removeClassName = function (name) {
  var parts = this.className.split(" ");
  var newParts = [];
  for (var i = 0; i < parts.length; i++) {
    if (parts[i] != name)
      newParts.push(parts[i]);
  }
  this.className = newParts.join(" ");
};

Element.prototype.setVisible = function (value) {
  this.style.visibility = value ? "inherit" : "hidden";
  this.style.display = value ? "inherit" : "none";
};

Element.prototype.setEnabled = function (value) {
  this.style.color = value ? "inherit" : "grey";
};

HTMLInputElement.prototype.setEnabled = HTMLSelectElement.prototype.setEnabled = function (value) {
  if (value) {
    this.removeAttribute('disabled');
  } else {
    this.setAttribute('disabled', 'disabled');
  }
};

/**
 * Standard base-class-instance-as-prototype based function
 * inheritance.
 */
Function.prototype.inherit = function (base) {
  function Inheriter() { }
  Inheriter.prototype = base.prototype;
  this.prototype = new Inheriter();
  this.baseClass = base;
};

Function.prototype.bind = function (self) {
  var fun = this;
  var outerArgs = arguments;
  return function () {
    var args = [];
    for (var i = 1; i < outerArgs.length; i++)
      args.push(outerArgs[i]);
    for (var i = 0; i < arguments.length; i++)
      args.push(arguments[i]);
    return fun.apply(self, args);
  };
};

/**
 * Returns a method that, when called, invokes this method with the given
 * arguments for all elements in the field 'name'.
 */
Function.prototype.mapOverField = function (name) {
  var fun = this;
  return function () {
    var args = [];
    for (var i = 0; i < arguments.length; i++)
      args.push(arguments[i]);
    var objs = this[name];
    for (var i = 0; i < objs.length; i++)
      fun.apply(objs[i], args);
  }
};

function unJson(obj) {
  var result = [];
  for (var prop in obj) {
    result.push(prop + ":" + obj[prop]);
  }
  return "{" + result.join(", ") + "}";
}

/* --------------- *
 * --- Promise --- *
 * --------------- */

/**
 * A delayed value.  Use .onValue to wait for the value to be
 * resolved.
 */
blogspotty.Promise = Promise;
function Promise() {
  this.state_ = Promise.STATE_OPEN;
  this.value_ = undefined;
  this.onValues_ = [];
  this.onErrors_ = [];
};

Promise.STATE_OPEN = "open";
Promise.STATE_HAS_VALUE = "has_value";
Promise.STATE_HAS_ERROR = "has_error";

Promise.yield = function (timeoutOpt) {
  var pResult = new Promise();
  window.setTimeout(function () { pResult.fulfill(null); }, timeoutOpt);
  return pResult;
};

/**
 * Resolve the value of this promise.  Anyone waiting for this promise
 * will be notified immediately, before this call returns.
 */
Promise.prototype.fulfill = function (value) {
  if (this.state_ == Promise.STATE_OPEN) {
    this.state_ = Promise.STATE_HAS_VALUE;
    this.value_ = value;
    this._fire(this.onValues_);
  }
};

Promise.prototype.hadError = function (message) {
  if (this.state_ == Promise.STATE_OPEN) {
    this.state_ = Promise.STATE_HAS_ERROR;
    this.value_ = message;
    if (this.onErrors_.length > 0) {
      this._fire(this.onErrors_);
    } else {
      logError(message);
    }
  }
};

function logError(str) {
  if (window.wave) {
    wave.log(str);
  }
}

/**
 * Notify waiting thunks that the value is now available.
 */
Promise.prototype._fire = function (waiters) {
  for (var i = 0; i < waiters.length; i++) {
    var fun = waiters[i];
    fun(this.value_);
  }
  waiters.length = 0;
};

Promise.prototype.onValue = function (fun) {
  if (this.state_ == Promise.STATE_OPEN) {
    this.onValues_.push(fun);
  } else if (this.state_ == Promise.STATE_HAS_VALUE) {
    fun(this.value_);
  }
};

Promise.prototype.onError = function (fun) {
  if (this.state_ == Promise.STATE_OPEN) {
    this.onErrors_.push(fun);
  } else if (this.state_ == Promise.STATE_HAS_ERROR) {
    fun(this.value_);
  }
};

/* ----------------- *
 * --- Templates --- *
 * ------------------*/

function Template(tag, props, children) {
  this.tag_ = tag;
  this.props_ = props;
  this.children_ = children;
}

var kAttributes = {colspan: true, align: true};

Template.prototype.materialize = function (parent) {
  var node;
  if (this.tag_.isString()) {
    switch (this.tag_) {
      case 'text':
        node = document.createTextNode('');
        break;
      default:
        node = document.createElement(this.tag_);
        break;
    }
  } else {
    node = this.tag_.materialize(parent);
  }
  for (var name in this.props_) {
    var value = this.props_[name];
    if (typeof value == 'function')
      continue;
    if (kAttributes[name]) {
      node.setAttribute(name, this.props_[name]);
    } else if (name == 'className') {
      node.addClassName(this.props_[name]);
    } else {
      node[name] = this.props_[name];
    }
  }
  for (var i = 0; i < this.children_.length; i++) {
    var child = this.children_[i].materialize(node);
    node.appendChild(child);
  }
  return node;
};

Template.prototype.render = function (root) {
  var node = this.materialize(root);
  root.appendChild(node);
  return node;
};

function Binder(callback, template) {
  this.callback_ = callback;
  this.template_ = template;
}

Binder.prototype.materialize = function (parent) {
  var result = this.template_.materialize(parent);
  this.callback_(result);
  return result;
};

function Splice(templates) {
  this.templates_ = templates;
}

Splice.prototype.render = function (parent) {
  var children = [];
  for (var i = 0; i < this.templates_.length; i++) {
    var template = this.templates_[i];
    var node = template.materialize(parent);
    parent.appendChild(node);
    children.push(node);
  }
  return new Spliced(children);
};

function Spliced(elms) {
  this.elms_ = elms;
}

Spliced.prototype.setVisible = Element.prototype.setVisible.mapOverField('elms_');
Spliced.prototype.addClassName = Element.prototype.addClassName.mapOverField('elms_');
Spliced.prototype.removeClassName = Element.prototype.removeClassName.mapOverField('elms_');

function e(tag, propsOpt, childrenOpt) {
  if (propsOpt !== undefined) {
    if (propsOpt.isArray()) {
      childrenOpt = propsOpt;
      propsOpt = {};
    } else if (propsOpt.isString()) {
      propsOpt = {'className': propsOpt};
    }
  }
  return new Template(tag, (propsOpt === undefined) ? {} : propsOpt,
    (childrenOpt === undefined) ? [] : childrenOpt);
}

function b(elm) {
  return e('b', [elm]);
}

function i(elm) {
  return e('i', [elm]);
}

function t(value) {
  return new Template("text", {'data': value}, []);
}

function x(name, template) {
  return new Binder(name, template);
}

function q(elms) {
  return new Splice(elms);
}

/* --------------- *
 * --- Control --- *
 * --------------- */
 
function Control() {
  this.template_ = null;
};

Control.prototype.getTemplate = function () {
  if (this.template_ == null)
    this.template_ = this.buildTemplate();
  return this.template_;
}

Control.prototype.render = function (root) {
  return root.appendChild(this.materialize(root));
};

Control.prototype.materialize = function (parent) {
  var template = this.getTemplate();
  return template.materialize(parent);
};

/* ------------------- *
 * --- Tab Control --- *
 * ------------------- */

function Tab(tabs, label) {
  this.tabs_ = tabs;
  this.label_ = label;
  this.onclick = null;
  this.node_ = null;
  this.contents_ = null;
  this.control_ = null;
  this.isSelected_ = false;
}

/**
 * Sets the node that contains this tabs header.
 */
Tab.prototype.setNode = function (node) {
  this.node_ = node;
  node.onclick = this.tabs_.onClicked.bind(this.tabs_, this);
  return node;
};

Tab.prototype.hasBeenRendered = function () {
  return this.contents_ != null;
};

Tab.prototype.setControl = function (control) {
  this.control_ = control;
};

Tab.prototype.setSelected = function (isSelected, parent) {
  if (isSelected == this.isSelected_)
    return;
  this.isSelected_ = isSelected;
  var contents = this.getContents(parent);
  if (isSelected) {
    this.node_.addClassName("dark");
    contents.setVisible(true);
  } else {
    this.node_.removeClassName("dark");
    contents.setVisible(false);
  }
};

Tab.prototype.getContents = function (parent) {
  if (!this.contents_) {
    this.contents_ = this.control_.getTemplate().render(parent);
    this.control_.onCreated();
    this.contents_.setVisible(false);
    this.contents_.addClassName('tabContents');
  }
  return this.contents_;
}

Tab.prototype.select = function () {
  this.tabs_.selectTab(this);
};

Tab.prototype.buildTemplate = function () {
  return (
    x(this.setNode.bind(this),
      e("div", "tabHeader", [
        e("div", "tabTopLeftCorner"),
        e("div", "top tabHorizontalEdge"),
        e("div", "tabTopRightCorner"),
        e("div", "left tabVerticalEdge"),
        e("div", "tabHeaderLabel", [
          t(this.label_)]
        ),
        e("div", "right tabVerticalEdge"),
        e("div", "bottom left tabSquareCorner"),
        e("div", "bottom right tabSquareCorner"),
      ])
    )
  )
};

TabControl.inherit(Control);
function TabControl() {
  this.tabs_ = [];
  this.center_ = null;
}

TabControl.prototype.render = function (root) {
  var result = Control.prototype.render.call(this, root);
  this.selectTab(this.tabs_[0]);
  return result;
}

TabControl.prototype.buildTemplate = function () {
  return (
    e("div", "tabControl", [
      e("div", "tabHeader", this.buildHeaderTemplate()),
      e("div", "dark tabBody", [
        e("div", "top left tabSquareCorner"),
        e("div", "top tabHorizontalEdge"),
        e("div", "tabTopRightCorner"),
        e("div", "left tabVerticalEdge"),
        x(this.setCenter.bind(this), e("div", "tabCenter")),
        e("div", "right tabVerticalEdge"),
        e("div", "tabBottomLeftCorner"),
        e("div", "bottom tabHorizontalEdge"),
        e("div", "tabBottomRightCorner"),
      ])
    ])
  )
};

TabControl.prototype.setCenter = function (center) {
  this.center_ = center;
};

TabControl.prototype.buildHeaderTemplate = function () {
  var tabs = [];
  for (var i = 0; i < this.tabs_.length; i++) {
    var tab = this.tabs_[i];
    tabs.push(e("div", "tabSingleHeader", [tab.buildTemplate()]));
  }
  return tabs;
};

TabControl.prototype.selectTab = function (tab) {
  for (var i = 0; i < this.tabs_.length; i++) {
    var next = this.tabs_[i];
    next.setSelected(next == tab, this.center_);
  }  
};

TabControl.prototype.onClicked = function (tab) {
  this.selectTab(tab);
  if (tab.onclick)
    tab.onclick();
};

TabControl.prototype.addTab = function (name) {
  var tab = new Tab(this, name);
  this.tabs_.push(tab);
  return tab;
};

/* --------------- *
 * --- Summary --- *
 * --------------- */

Summary.inherit(Control);
function Summary(controller) {
  this.isLive_ = false;
  this.isDraft_ = false;
  this.root_ = null;
  this.logInSummary_ = SummaryType.logIn();
  this.loggingInSummary_ = SummaryType.loggingIn();
  this.connectedSummary_ = new ConnectedSummaryType(controller);
  this.currentSummary_ = null;
}

Summary.prototype.onCreated = function (root) {
  this.root_ = root;
}

Summary.prototype.buildTemplate = function () {
  return x(this.onCreated.bind(this), e("div", {className: "summary", align: "center"}));
};

Summary.prototype.onStateChanged = function (state) {
  switch (state.getStatus()) {
    case Gadget.LOGIN:
      this.select(this.logInSummary_);
      break;
    case Gadget.LOGGING_IN:
      this.select(this.loggingInSummary_);
      break;
    case Gadget.CONNECTED:
      this.select(this.connectedSummary_);
      break;
    default:
      this.select(null);
      break;
  }
  if (this.currentSummary_)
    this.currentSummary_.onStateChanged(state);
};

Summary.prototype.select = function (summary) {
  if (summary === this.currentSummary_)
    return;
  if (this.currentSummary_ != null)
    this.currentSummary_.setVisible(false);
  this.currentSummary_ = summary;
  if (summary != null) {
    summary.ensureRendered(this.root_);
    summary.setVisible(true);
  }
}

function SummaryType(templateOpt) {
  this.template_ = templateOpt;
  this.node_ = null;
}

SummaryType.prototype.setVisible = function (value) {
  this.node_.setVisible(value);
};

SummaryType.prototype.onStateChanged = function (state) {
  // ignore
};

SummaryType.prototype.ensureRendered = function (root) {
  if (!this.node_) {
    this.ensureSummaryTemplate();
    this.node_ = this.template_.render(root);
  }
}

SummaryType.prototype.ensureSummaryTemplate = function () {
  if (!this.template_)
    this.template_ = this.buildSummaryTemplate();
};

SummaryType.logIn = function () {
  return new SummaryType(
    e("div", [t("Log in to start publishing this wave on blogger.")])
  );
};

SummaryType.loggingIn = function () {
  return new SummaryType(
    e("div", [t("Logging in to blogger in a new window.")])
  );
};

ConnectedSummaryType.inherit(SummaryType);
function ConnectedSummaryType(controller) {
  SummaryType.call(this);
  this.body_ = null;
  this.controller_ = controller;
}

ConnectedSummaryType.prototype.onCreated = function (body) {
  this.body_ = body;
};

ConnectedSummaryType.prototype.buildSummaryTemplate = function () {
  return e("div", "connectedSummary", [x(this.onCreated.bind(this), e("div"))])
};

ConnectedSummaryType.prototype.onStateChanged = function (state) {
  var mode = state.getPublishMode();
  var text = [];
  var controller = this.controller_;
  var owner = controller.getOwner();
  // Allow line breaks before '.' and '@' in the username.
  if (owner)
    owner = owner.replace(".", ".&#8203;").replace("@", "@&#8203;");
  text.push("Connected to <i>" + controller.getBlogName() + "</i> by " + owner + ".");
  var time = state.getPostTime();
  if (time) {
    var title = state.getPostTitle();
    var url = state.getPostUrl();
    var hour = ("00" + time.getHours()).slice(-2);
    var min = ("00" + time.getMinutes()).slice(-2);
    var when = time.toDateString() + " at " + hour + ":" + min;
    var what, where = '';
    if (state.getPublishMode() == Gadget.PUBLISH_DRAFT) {
      what = "saved as draft ";
    } else {
      what = 'published';
      if (title && url) {
        where = ' as <a target="_blank" href="' + url + '">' +
            title + "</a> ";
      }
    }
    text.push('Last ' + what + where + " on " + when + ".");
  }
  this.body_.innerHTML = text.join(" ");
};

/* -------------- *
 * --- Action --- *
 * -------------- */

MainAction.inherit(Control);
function MainAction(controller) {
  Control.call(this);
  this.root_ = null;
  this.publishAction_ = new PublishAction(controller);
  this.logInAction_ = new LogInAction(controller);
  this.doneLoggingInAction_ = new DoneLoggingInAction(controller);
  this.currentAction_ = null;
}

MainAction.prototype.onCreated = function (root) {
  this.root_ = root;
};

MainAction.prototype.buildTemplate = function () {
  return x(this.onCreated.bind(this), e("div", {className: "actions", align: "center"}));
};

MainAction.prototype.onStateChanged = function (state) {
  switch (state.getStatus()) {
    case Gadget.LOGIN:
      this.select(this.logInAction_);
      break;
    case Gadget.LOGGING_IN:
      this.select(this.doneLoggingInAction_);
      break;
    default:
      this.select(this.publishAction_);
      break;
  }
  if (this.currentAction_ != null)
    this.currentAction_.onStateChanged(state);
};

MainAction.prototype.select = function (type) {
  if (type !== this.currentAction_) {
    if (this.currentAction_ != null)
      this.currentAction_.setVisible(false);
    type.ensureRendered(this.root_);
    type.setVisible(true);
    this.currentAction_ = type;
  }
}

function MainActionType(controller, templateOpt) {
  Control.call(this);
  this.controller_ = controller;
  this.template_ = templateOpt;
  this.node_ = null;
}

MainActionType.prototype.onStateChanged = function (state) {
  // ignore
};

MainActionType.prototype.ensureRendered = function (root) {
  if (!this.node_)
    this.node_ = this.buildTemplate().render(root);
}

MainActionType.prototype.setVisible = function (value) {
  this.node_.setVisible(value);
};

MainActionType.prototype.buildTemplate = function () {
  if (this.template_ == null)
    this.template_ = this.buildTemplate();
  return this.template_;
};

MainActionType.prototype.getController = function () {
  return this.controller_;
};

/* --- Publish action --- */

PublishAction.inherit(MainActionType);
function PublishAction(controller) {
  MainActionType.call(this, controller);
  this.autoPublish_ = null;
  this.publish_ = null;
  this.saveDraft_ = null;
}

PublishAction.prototype.onStateChanged = function (state) {
  var isEnabled = false;
  if (state.getStatus() == Gadget.CONNECTED) {
    if (state.getPublishRights() == Gadget.PUBLISH_RIGHTS_OWNER) {
      isEnabled = this.getController().isOwner();
    } else if (state.getPublishRights() == Gadget.PUBLISH_RIGHTS_ANYONE) {
      isEnabled = true;
    }
  }
  this.autoPublish_.setEnabled(isEnabled);
  this.publish_.setEnabled(isEnabled);
  this.saveDraft_.setEnabled(isEnabled);
  var publishMode = state.getPublishMode();
  this.autoPublish_.setGlowing(publishMode == Gadget.PUBLISH_AUTO);
  this.publish_.setGlowing(publishMode == Gadget.PUBLISH_MANUAL);
  this.saveDraft_.setGlowing(publishMode == Gadget.PUBLISH_DRAFT);
};

PublishAction.prototype.buildTemplate = function () {
  this.autoPublish_ = new HaloButton("Auto publish", true);
  this.autoPublish_.addClickListener((function () {
    this.getController().onAutoPublishClicked();
  }).bind(this));
  this.publish_ = new HaloButton("Publish", true);
  this.publish_.addClickListener((function () {
    this.getController().onPublishClicked();
  }).bind(this));
  this.saveDraft_ = new HaloButton("Save draft", true);
  this.saveDraft_.addClickListener((function () {
    this.getController().onSaveDraftClicked();
  }).bind(this))
  return q([
    e("div", "leftPublishButton", [this.autoPublish_]),
    e("div", "centerPublishButton", [this.publish_]),
    e("div", "rightPublishButton", [this.saveDraft_]),
  ]);
};

/* --- Log in action --- */

LogInAction.inherit(MainActionType);
function LogInAction(controller) {
  MainActionType.call(this, controller);
}

LogInAction.prototype.buildTemplate = function () {
  var controller = this.getController();
  var button = new Button("Log in", true);
  button.setEnabled(false);
  controller.getBlogger().getOAuthPopup().onValue(function (popup) {
    button.addClickListener(popup.createOpenerOnClick());
    button.setEnabled(true);
  });
  return e("div", "centerActionButton", [button])
};

/* --- Done logging in action --- */

DoneLoggingInAction.inherit(MainActionType);
function DoneLoggingInAction(controller) {
  MainActionType.call(this, controller);
}

DoneLoggingInAction.prototype.buildTemplate = function () {
  var button = new Button("Done", true);
  button.setEnabled(false);
  var controller = this.getController();
  controller.getBlogger().getOAuthPopup().onValue(function (popup) {
    button.addClickListener(popup.createApprovedOnClick());
    button.setEnabled(true);
  });
  return e("div", "centerActionButton", [button]);
};

/* -------------- *
 * --- Button --- *
 * -------------- */

Button.inherit(Control);
function Button(label, isActive) {
  this.label_ = label;
  this.isActive_ = isActive;
  this.middle_ = null;
  this.isEnabled_ = true;
  this.listeners_ = [];
}

Button.prototype.addClickListener = function (listener) {
  this.listeners_.push(listener);
};

Button.prototype.setEnabled = function (value) {
  this.isEnabled_ = value;
  this.updateEnablement();
};

Button.prototype.updateEnablement = function () {
  if (this.middle_ != null) {
    if (this.isEnabled_) {
      this.middle_.addClassName("enabled");
      this.middle_.removeClassName("disabled");
    } else {
      this.middle_.addClassName("disabled");
      this.middle_.removeClassName("enabled");
    }
  }
};

Button.prototype.setOuter = function (outer) {
  outer.onmousedown = function () {
    outer.addClassName("down");
  };
  outer.onmouseup = outer.onmouseout = function () {
    outer.removeClassName("down")
  };
  outer.onclick = this.fireClicked.bind(this);
};

Button.prototype.fireClicked = function () {
  if (this.isEnabled_) {
    for (var i = 0; i < this.listeners_.length; i++) {
      var listener = this.listeners_[i];
      listener();
    }
  }
};

Button.prototype.setMiddle = function (middle) {
  this.middle_ = middle;
  this.updateEnablement();
};

Button.prototype.setInner = function (inner) {
  inner.addClassName(this.isActive_ ? "active" : "passive");
};

Button.prototype.buildTemplate = function () {
  return (
    x(this.setOuter.bind(this),
      e('div', "button", [
        x(this.setMiddle.bind(this),
          e('div', [
            x(this.setInner.bind(this),
              e('div', [
                e('div', 'buttonLeft'),
                e('div', 'buttonMiddle', [
                  e('span', 'buttonLabel', [t(this.label_)]),
                ]),
                e('div', 'buttonRight')
              ])
            )
          ])
        )
      ])
    )
  );
};

/* ------------------- *
 * --- Halo Button --- *
* ------------------- */

HaloButton.inherit(Button);
function HaloButton(label, isActive) {
  Button.call(this, label, isActive);
  this.haloOuter_ = null;
  this.isGlowing_ = false;
}

HaloButton.prototype.setGlowing = function (value) {
  this.isGlowing_ = value;
  this.updateGlowingness();
}

HaloButton.prototype.setHaloOuter = function (outer) {
  this.haloOuter_ = outer;
  this.updateGlowingness();
};

HaloButton.prototype.setHaloMiddle = function (middle) {
  this.haloMiddle_ = middle;
  this.updateEnablement();
};

HaloButton.prototype.updateEnablement = function () {
  Button.prototype.updateEnablement.call(this);
  if (this.haloMiddle_) {
    if (this.isEnabled_) {
      this.haloMiddle_.removeClassName("disabled");
    } else {
      this.haloMiddle_.addClassName("disabled");
    }
  }
};

HaloButton.prototype.updateGlowingness = function () {
  if (this.haloOuter_) {
    if (this.isGlowing_) {
      this.haloOuter_.addClassName("glow");
    } else {
      this.haloOuter_.removeClassName("glow");
    }
  }
};

HaloButton.prototype.buildTemplate = function () {
  return (
    x(this.setHaloOuter.bind(this),
      e("div", "haloButtonOuter", [
        x(this.setHaloMiddle.bind(this),
          e("div", "haloButtonMiddle", [
            e("div", "haloTopLeft"),
            e("div", "haloTopRight"),
            e("div", "haloBottomLeft"),
            e("div", "haloBottomRight"),
            e("div", "top haloHorizontalEdge"),
            e("div", "bottom haloHorizontalEdge"),
            e("div", "left haloVerticalEdge"),
            e("div", "right haloVerticalEdge"),
            e("div", "haloButtonInner", [
              Button.prototype.buildTemplate.call(this)
            ])
          ])
        )
      ])
    )
  );
};


/* ------------------- *
 * --- Gadget tabs --- *
 * ------------------- */

function GadgetTab(tab, controller) {
  this.tab_ = tab;
  this.controller_ = controller;
  tab.setControl(this);
}

GadgetTab.prototype.onCreated = function () {
  var state = this.controller_.getStateWrapper()
  if (state)
    this.onStateChanged(state);
};

GadgetTab.prototype.select = function () {
  this.tab_.select();
};

GadgetTab.prototype.onStateChanged = function () {
  // ignore
};

GadgetTab.prototype.hasBeenRendered = function () {
  return this.tab_.hasBeenRendered();
};

/* ------------------- *
 * --- Publish tab --- *
 * ------------------- */

PublishTab.inherit(GadgetTab);
function PublishTab(tabs, controller) {
  GadgetTab.call(this, tabs.addTab("Publish"), controller);
  this.summary_ = new Summary(controller);
  this.action_ = new MainAction(controller);
}

PublishTab.prototype.onStateChanged = function (state) {
  this.summary_.onStateChanged(state);
  this.action_.onStateChanged(state);
};

PublishTab.prototype.getTemplate = function () {
  return (
    e('div', "publishOuter", [
      e("div", "publishBlock", [
        e("table", "summaryTable", [
          e("tr", [
            e("td", [this.summary_])
          ])
        ])
      ]),
      e('div', "publishOuter", [
        e("div", "publishBlock", [
          e("table", "actionTable", [
            e("tr", [
              e("td", [this.action_])
            ])
          ])
        ]),
      ])
    ])
  )
};

/* -------------------- *
 * --- Settings tab --- *
 * -------------------- */

function TransientState(controller) {
  this.state_ = null;
  this.settings_ = {};
  this.wrapper_ = null;
  this.listeners_ = [];
  this.controller_ = controller;
};

TransientState.prototype.addChangeListener = function (listener) {
  this.listeners_.push(listener);
};

TransientState.prototype.fireOnChanged = function () {
  for (var i = 0; i < this.listeners_.length; i++) {
    var listener = this.listeners_[i];
    listener(this.wrapper_);
  }
};

TransientState.prototype.onStateChanged = function (state) {
  this.state_ = state;
  this.wrapper_ = new StateWrapper(this);
  var oldSettings = this.settings_;
  this.settings_ = {};
  for (var key in oldSettings) {
    var value = oldSettings[key];
    if (value != 'function')
      this.set(key, oldSettings[key]);
  }
  this.fireOnChanged();
};

TransientState.prototype.get = function (key, ifMissing) {
  if (key in this.settings_) {
    return this.settings_[key];
  } else {
    return this.state_.getRaw(key, ifMissing);
  }
};

TransientState.prototype.reset = function () {
  this.settings_ = {};
  this.fireOnChanged();
};

TransientState.prototype.apply = function () {
  this.state_.update(this.settings_);
};

TransientState.prototype.setPublishRights = function (value) {
  this.set(Gadget.PUBLISH_RIGHTS_KEY, value);
};

TransientState.prototype.setBlog = function (value) {
  this.set(Gadget.BLOG_KEY, value);
};

TransientState.prototype.set = function (key, value) {
  if (this.settings_[key] == value) {
    return;
  }
  if (this.state_.getRaw(key, StateWrapper.DEFAULTS[key]) == value) {
    delete this.settings_[key];
  } else {
    this.settings_[key] = value;
  }
  this.fireOnChanged();
};

TransientState.prototype.hasChanges = function () {
  for (var name in this.settings_) {
    if (typeof this.settings_[name] != 'function')
      return true;
  }
  return false;
};

SettingsTab.inherit(GadgetTab);
function SettingsTab(tabs, controller) {
  GadgetTab.call(this, tabs.addTab("Settings"), controller);
  this.controller_ = controller;
  this.blogList_ = null;
  this.elms_ = [];
  this.currentState_ = new TransientState(controller);
  this.currentState_.addChangeListener(this.onTransientStateChanged.bind(this));
};

SettingsTab.prototype.onStateChanged = function (rawState) {
  this.getCurrentState().onStateChanged(rawState);
};

SettingsTab.prototype.isRendered = function () {
  return this.blogList_ != null;
};

SettingsTab.prototype.onTransientStateChanged = function (state) {
  if (this.isRendered()) {
    var isConnected = state.getStatus() == Gadget.CONNECTED;
    this.setEnabled(isConnected && this.controller_.isOwner());
    this.updateBlogList(state.getBlogs(), state.getBlog());
  }
};

SettingsTab.prototype.updateBlogList = function (blogs, selected) {
  if (blogs === null) {
    this.blogList_.setEnabled(false);
    this.blogList_.innerHTML = "<option>Not connected</option>";
  } else if (blogs.length == 0) {
    this.blogList_.setEnabled(false);
    this.blogList_.innerHTML = "<option>No blogs</option>";
  } else {
    this.blogList_.innerHTML = '';
    for (var i = 0; i < blogs.length; i++) {
      var blog = blogs[i];
      var option = document.createElement('option');
      var label = document.createTextNode(blog.title);
      option.appendChild(label);
      this.blogList_.appendChild(option);
      if (blogs[i].id == selected) {
        option.setAttribute('selected', 'selected');
      }
      option.value = blogs[i].id;
    }
  }
};

SettingsTab.prototype.setEnabled = function (enabled) {
  for (var i = 0; i < this.elms_.length; i++) {
    this.elms_[i].setEnabled(enabled);
  }
};

SettingsTab.prototype.onPublishModeChanged = function (value) {
  this.getCurrentState().setPublishMode(value);
};

SettingsTab.prototype.onBlogSelected = function (id) {
  this.getCurrentState().setBlog(id);
};

SettingsTab.prototype.onPublishRightsChanged = function (allowOthers) {
  this.getCurrentState().setPublishRights(allowOthers
     ? Gadget.PUBLISH_RIGHTS_ANYONE
     : Gadget.PUBLISH_RIGHTS_OWNER);
};

SettingsTab.prototype.onResetClicked = function () {
  this.getCurrentState().reset();
};

SettingsTab.prototype.onApplyClicked = function () {
  this.getCurrentState().apply();
};

SettingsTab.prototype.makeCheckBox = function (label, classOpt, onCreatedOpt) {
  function onElementCreated(check) {
    if (onCreatedOpt)
      onCreatedOpt(check);
    this.elms_.push(check);
  }
  return (
    e('div', classOpt ? classOpt : {}, [
      x(onElementCreated.bind(this),
        e('input', {type: 'checkbox'})),
      x(onElementCreated.bind(this),
        e('span', label))
    ])
  );
};

SettingsTab.prototype.setBlogList = function (blogList) {
  this.blogList_ = blogList;
  this.elms_.push(blogList);
  blogList.onchange = (function (event) {
    this.onBlogSelected(blogList.value);
  }).bind(this);
};

SettingsTab.prototype.getCurrentState = function () {
  return this.currentState_;
};

SettingsTab.prototype.onPublishRightsCreated = function (node) {
  node.onchange = (function () {
    this.onPublishRightsChanged(node.checked);
  }).bind(this);
};

SettingsTab.prototype.getTemplate = function () {
  var applyButton = new Button("Apply", true);
  applyButton.addClickListener(this.onApplyClicked.bind(this));
  this.elms_.push(applyButton);
  var resetButton = new Button("Reset", false);
  resetButton.addClickListener(this.onResetClicked.bind(this));
  this.elms_.push(resetButton);
  var makeDefaultButton = new Button("Make default", false);
  this.elms_.push(makeDefaultButton);
  this.getCurrentState().addChangeListener((function () {
    var hasChanges = this.getCurrentState().hasChanges();
    applyButton.setEnabled(hasChanges);
    resetButton.setEnabled(hasChanges);
    makeDefaultButton.setEnabled(hasChanges);
  }).bind(this));
  function onElementCreated(elm) {
    this.elms_.push(elm);
  }
  var w = (function (template) {
    return x(onElementCreated.bind(this), template);
  }).bind(this);
  return q([
    e('div', 'tabContents settings', [
      w(
        e('div', [
          t('Where do you want to publish this wave?')
        ])
      ),
      e('div', [
        x(
          this.setBlogList.bind(this), 
          e('select')
        )
      ]),
      w(
        e('div', "innerLabel", [
          t('Who controls how this wave is published?')
        ])
      ),
      this.makeCheckBox(
        [t('Allow '), b(t('all participants')), t(' to publish.')],
        undefined,
        this.onPublishRightsCreated.bind(this)),
      w(
        e('div', "innerLabel workInProgress", [
          t("How should comments be delievered?")
        ])
      ),
      this.makeCheckBox([t('Show '), b(t('comments as replies')), t(' to this wave.')], "workInProgress"),
      this.makeCheckBox([t('Post '), b(t('replies as comments')), t(' on the blog.')], "workInProgress")
    ]),
    e('div', "settingsButtons", [
      e(applyButton, "settingsButton"),
      e(resetButton, "settingsButton"),
      e(makeDefaultButton, 'settingsButton workInProgress'),
    ])
  ]);
};

/* ------------------ *
 * --- Images tab --- *
 * ------------------ */
 
ImagesTab.inherit(GadgetTab);
function ImagesTab(tabs, controller) {
  GadgetTab.call(this, tabs.addTab("Images"), controller);
}

ImagesTab.prototype.getTemplate = function () {
  return e('div', 'tabContents', [t('Images')]);
};

/* ------------------- *
 * --- Gadget view --- *
 * ------------------- */

var kShowImagesTab = false;
function GadgetView(backend, controller) {
  this.tabs_ = new TabControl();
  this.publish_ = new PublishTab(this.tabs_, controller);
  this.settings_ = new SettingsTab(this.tabs_, controller);
  if (kShowImagesTab)
    this.images_ = new ImagesTab(this.tabs_, controller);
  this.node_ = null;
}

GadgetView.prototype.render = function (parent) {
  this.node_ = this.tabs_.render(parent);
  this.node_.addClassName("gadget");
};

GadgetView.prototype.onStateChanged = function (state, initial) {
  this.publish_.onStateChanged(state);
  this.settings_.onStateChanged(state);
  if (kShowImagesTab)
    this.images_.onStateChanged(state);
};

GadgetView.prototype.showSettings = function () {
  this.settings_.select();
};

/* -------------------------- *
 * --- Blogger connection --- *
 * -------------------------- */

function Blogger(controller) {
  this.controller_ = controller;
  this.service_ = null;
  this.pOAuthLoginUrl_ = new Promise();
  this.pOAuthPopup_ = new Promise();
}

Blogger.SCOPE = 'http://www.blogger.com/feeds';

Blogger.prototype.init = function (userid, waveid) {
  Request.toServer('authUrl', {
    userid: userid,
    waveid: waveid
  }).onValue(this.onReceivedAuthUrl.bind(this));
};

Blogger.prototype.getOAuthLoginUrl = function () {
  return this.pOAuthLoginUrl_;
};

Blogger.prototype.getOAuthPopup = function () {
  return this.pOAuthPopup_;
};

Blogger.prototype.onReceivedAuthUrl = function (data) {
  var url = data.url;
  this.pOAuthLoginUrl_.fulfill(url);
  var controller = this.controller_;
  var popup = new gadgets.oauth.Popup(url, 'height=600,width=700',
    controller.onAuthPopupOpened.bind(controller),
    controller.onAuthPopupClosed.bind(controller));
  this.pOAuthPopup_.fulfill(popup);
};

/* -------------- *
 * --- Gadget --- *
 * -------------- */

blogspotty.Gadget = Gadget;
function Gadget(state, backend) {
  this.state_ = state;
  this.state_.addChangeListener(this.onStateChanged.bind(this));
  this.backend_ = backend;
  this.getBackend().getLoaded().onValue(this.onBackendLoaded.bind(this));
  this.hasInitialState_ = false;
  this.view_ = new GadgetView(backend, this);
  this.blogger_ = new Blogger(this);
};

Gadget.STATUS_KEY = 'status';
Gadget.LOGIN = 'login';
Gadget.LOGGING_IN = 'logging_in';
Gadget.LOGGED_IN = 'logged_in';
Gadget.CONNECTED = 'connected';

Gadget.PUBLISH_MODE_KEY = 'publish_mode';
Gadget.PUBLISH_NONE = 'none';
Gadget.PUBLISH_AUTO = 'auto';
Gadget.PUBLISH_MANUAL = 'manual';
Gadget.PUBLISH_DRAFT = 'draft';

Gadget.PUBLISH_RIGHTS_KEY = 'publish_rights';
Gadget.PUBLISH_RIGHTS_OWNER = 'owner';
Gadget.PUBLISH_RIGHTS_ANYONE = 'anyone';

Gadget.REQUEST_KEY = 'request';
Gadget.REQUEST_CONNECT = 'connect';
Gadget.REQUEST_PUBLISH = 'publish';
Gadget.REQUEST_SAVE_DRAFT = 'save_draft';
Gadget.REQUEST_NONE = 'none';

Gadget.OWNER_KEY = 'owner';
Gadget.BLOGS_KEY = 'blogs';
Gadget.BLOG_KEY = 'blog';
Gadget.URL_KEY = 'post_url';
Gadget.TITLE_KEY = 'post_title';
Gadget.POST_TIME_KEY = 'post_time';


Gadget.prototype.checkLogin = function () {
  Request.toServer('authCheck', {
    userid: this.getUserId(),
    waveid: this.getWaveId()
  }).onValue(this.onCheckedLogin.bind(this));
};

Gadget.prototype.onCheckedLogin = function (data) {
  if (data.isSignedIn) {
    var newState = {};
    newState[Gadget.STATUS_KEY] = Gadget.LOGGED_IN;
    newState[Gadget.REQUEST_KEY] = Gadget.REQUEST_CONNECT;
    this.getState().update(newState);
  } else {
    this.getState().clearTransient(Gadget.STATUS_KEY);
  }
};

Gadget.prototype.clearRequest = function () {
  var currentRequest = this.getState().get(Gadget.REQUEST_KEY, Gadget.REQUEST_NONE);
  if (currentRequest != Gadget.REQUEST_NONE) {
    var newState = {};
    newState[Gadget.REQUEST_KEY] = Gadget.REQUEST_NONE;
    this.getState().update(newState);
  }  
};

Gadget.prototype.onPublishClicked = function () {
  this.clearRequest();
  Promise.yield().onValue((function () {
    var newState = {};
    newState[Gadget.PUBLISH_MODE_KEY] = Gadget.PUBLISH_MANUAL;
    newState[Gadget.REQUEST_KEY] = Gadget.REQUEST_PUBLISH;
    this.getState().update(newState);
  }).bind(this));
};

Gadget.prototype.onAutoPublishClicked = function () {
  this.clearRequest();
  Promise.yield().onValue((function () {
    var newState = {};
    newState[Gadget.PUBLISH_MODE_KEY] = Gadget.PUBLISH_AUTO;
    newState[Gadget.REQUEST_KEY] = Gadget.REQUEST_PUBLISH;    
    this.getState().update(newState);
  }).bind(this));
};

Gadget.prototype.onSaveDraftClicked = function () {
  this.clearRequest();
  Promise.yield().onValue((function () {
    var newState = {};
    newState[Gadget.PUBLISH_MODE_KEY] = Gadget.PUBLISH_DRAFT;
    newState[Gadget.REQUEST_KEY] = Gadget.REQUEST_SAVE_DRAFT;    
    this.getState().update(newState);
  }).bind(this));
};

Gadget.prototype.onBackendLoaded = function () {
  this.getBlogger().init(this.getUserId(), this.getWaveId())
};

Gadget.prototype.onAuthPopupOpened = function () {
  this.getState().setTransient(Gadget.STATUS_KEY, Gadget.LOGGING_IN);
};

Gadget.prototype.onAuthPopupClosed = function () {
  this.checkLogin();
};

Gadget.prototype.getBlogger = function () {
  return this.blogger_;
};

Gadget.prototype.getView = function () {
  return this.view_;
};

Gadget.prototype.getState = function () {
  return this.hasInitialState_ ? this.state_ : null;
}

Gadget.prototype.onStateChanged = function (state) {
  this.hasInitialState_ = true;
  this.getView().onStateChanged(new StateWrapper(state), !this.hasInitialState_);
};

Gadget.prototype.getStateWrapper = function () {
  return this.hasInitialState_ ? new StateWrapper(this.state_) : null;
};

Gadget.prototype.getBackend = function () {
  return this.backend_;
};

Gadget.prototype.isOwner = function () {
  return this.getBackend().getUserId() == this.getOwner();
};

Gadget.prototype.getOwner = function () {
  return this.getStateWrapper().getOwner();
};

Gadget.prototype.getBlogName = function () {
  var blogs = this.getStateWrapper().getBlogs();
  if (!blogs)
    return null;
  var blog = this.getStateWrapper().getBlog();
  for (var i = 0; i < blogs.length; i++) {
    if (blogs[i].id == blog)
      return blogs[i].title;
  }
  return null;
};

Gadget.prototype.getUserId = function () {
  return this.getBackend().getUserId();
};

Gadget.prototype.getWaveId = function () {
  return this.getBackend().getWaveId();
};

function StateWrapper(state) {
  this.state_ = state;
  this.bloglist_ = null;
}

StateWrapper.DEFAULTS = {};
StateWrapper.DEFAULTS[Gadget.PUBLISH_RIGHTS_KEY] = Gadget.PUBLISH_RIGHTS_OWNER;
StateWrapper.DEFAULTS[Gadget.PUBLISH_MODE_KEY] = Gadget.PUBLISH_NONE;
StateWrapper.DEFAULTS[Gadget.STATUS_KEY] = Gadget.LOGIN;
StateWrapper.DEFAULTS[Gadget.BLOGS_KEY] = null;

StateWrapper.prototype.getStatus = function () {
  return this.getRaw(Gadget.STATUS_KEY);
};

StateWrapper.prototype.update = function (map) {
  this.state_.update(map);
}

StateWrapper.prototype.getPostTitle = function () {
  return this.getRaw(Gadget.TITLE_KEY);
};

StateWrapper.prototype.getPostUrl = function () {
  return this.getRaw(Gadget.URL_KEY);
};

StateWrapper.prototype.getPostTime = function () {
  var time = this.getRaw(Gadget.POST_TIME_KEY);
  if (time) {
    return new Date(time);
  } else {
    return null;
  }
};

StateWrapper.prototype.getPublishRights = function () {
  return this.getRaw(Gadget.PUBLISH_RIGHTS_KEY);
};

StateWrapper.prototype.getPublishMode = function () {
  return this.getRaw(Gadget.PUBLISH_MODE_KEY);
};

StateWrapper.prototype.getBlog = function () {
  return this.getRaw(Gadget.BLOG_KEY);
};

StateWrapper.prototype.getBlogs = function () {
  if (this.bloglist_ === null) {
    var str = this.getRaw(Gadget.BLOGS_KEY, null);
    if (str == null) {
      this.bloglist_ = null;
    } else {
      this.bloglist_ = eval("(" + str + ")");
    }
  }
  return this.bloglist_;
};

StateWrapper.prototype.getOwner = function () {
  return this.getRaw(Gadget.OWNER_KEY, null);
};

StateWrapper.prototype.getRaw = function (key) {
  return this.state_.get(key, StateWrapper.DEFAULTS[key]);
};

/* ------------------ *
 * --- Wave state --- *
 * ------------------ */

function WaveState(wave) {
  this.wave_ = wave;
  this.state_ = null;
  this.transient_ = {};
  this.listeners_ = [];
  wave.setStateCallback(this.onStateChanged.bind(this));
};

WaveState.prototype.addChangeListener = function (listener) {
  this.listeners_.push(listener);
};

WaveState.prototype.onStateChanged = function () {
  this.state_ = this.getWave().getState();
  this.transient_ = {};
  this.fireStateChanged();
};

WaveState.prototype.fireStateChanged = function () {
  for (var i = 0; i < this.listeners_.length; i++) {
    (this.listeners_[i])(this);
  }
};

WaveState.prototype.setTransient = function (key, value) {
  this.transient_[key] = value;
  Promise.yield().onValue(this.fireStateChanged.bind(this));
};

WaveState.prototype.update = function (map) {
  this.state_.submitDelta(map);
}

WaveState.prototype.clearTransient = function (key) {
  Promise.yield().onValue(this.fireStateChanged.bind(this));
  return delete this.transient_[key];
};

WaveState.prototype.get = function (name, ifMissing) {
  if (name in this.transient_)
    return this.transient_[name];
  var result = this.state_.get(name);
  if (result === null) {
    return ifMissing;
  } else {
    return result;
  }
};

WaveState.prototype.getWave = function () {
  return this.wave_;
};

/* --------------- *
 * --- Request --- *
 * --------------- */
 
function Request() { }

Request.SERVER = "https://blogspotty.appspot.com/server";

Request.toServer = function (path, args, typeOpt) {
  var url = Request.SERVER + "/" + path;
  return Request.make(url, args, typeOpt);
};

Request.make = function (url, args, typeOpt) {
  var pResult = new Promise();
  var first = true;
  for (var name in args) {
    if (typeof name != 'function') {
      if (first) {
        first = false;
        url += "?";
      } else {
        url += "&";
      }
      url += encodeURIComponent(name) + "=" + encodeURIComponent(args[name]);
    }
  }
  if (window.osapi && osapi.http && osapi.http.get) {
    osapi.http.get({
      href: url,
      format: (typeOpt || 'json'),
      authz: 'signed'
    }).execute(function (response) {
      if (response.error) {
        pResult.hadError(unJson(response.error));
      } else {
        pResult.fulfill(response.content);
      }
    });
  }
  return pResult;
}

/* -------------------- *
 * --- Wave backend --- *
 * -------------------- */

function WaveBackend(wave) {
  this.wave_ = wave;
  this.pLoaded_ = new Promise();
  this.isLoaded_ = false;
}

WaveBackend.prototype.getWave = function () {
  return this.wave_;
};

WaveBackend.prototype.getWaveId = function () {
  return this.getWave().getWaveId();
};

WaveBackend.prototype.getUserId = function () {
  return this.getWave().getViewer().getId();
};

WaveBackend.prototype.getLoaded = function () {
  return this.pLoaded_;
};

WaveBackend.prototype.onStateChanged = function () {
  if (!this.isLoaded_) {
    this.isLoaded_ = true;
    this.pLoaded_.fulfill(this);
  }
};

/* ------------ *
 * --- Main --- *
 * ------------ */

/**
 * Returns a promise that will be fulfilled when wave has been
 * successfully loaded and it has been verified that we are, in fact,
 * running in a wave container.  If neither of these are the case the
 * promise will never be fulfilled.
 */
function getWave() {
  var pResult = new Promise();
  if (window.gadgets && gadgets.util && gadgets.util.registerOnLoadHandler) {
    gadgets.util.registerOnLoadHandler(function () {
      if (window.wave && wave.isInWaveContainer())
        pResult.fulfill(wave);
    });
  }
  return pResult;
}

/**
 * Run when and if wave is successfully loaded.
 */
function onWaveLoaded(wave) {
  var state = new WaveState(wave);
  var backend = new WaveBackend(wave);
  var gadget = new Gadget(state, backend);
  state.addChangeListener(backend.onStateChanged.bind(backend));
  gadget.getView().render(document.getElementById('gadget'));
  gadgets.window.adjustHeight();
}

/**
 * Run as soon as the script has loaded.
 */
function onScriptLoaded() {
  getWave().onValue(onWaveLoaded);
}

// Let's go!
onScriptLoaded();

})();
