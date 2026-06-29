self.__MIDDLEWARE_MATCHERS = [
  {
    "regexp": "^(?:\\/(_next\\/data\\/[^/]{1,}))?(?:\\/((?!_next\\/|wizard\\/|favicon|assets\\/|.*\\.(?:css|js|png|jpg|jpeg|svg|gif|ico|woff2?|ttf)$).*))(\\\\.json)?[\\/#\\?]?$",
    "originalSource": "/((?!_next/|wizard/|favicon|assets/|.*\\.(?:css|js|png|jpg|jpeg|svg|gif|ico|woff2?|ttf)$).*)"
  }
];self.__MIDDLEWARE_MATCHERS_CB && self.__MIDDLEWARE_MATCHERS_CB()