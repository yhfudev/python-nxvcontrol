#!/bin/bash
# init languages

FN_TEMPLATE="nxvcontrol.pot"

parse_pyfile() {
    PARAM_FILE=$1
    shift

    if [ ! -f "${FN_TEMPLATE}" ]; then
        # xgettext --language=Python --keyword=_ --from-code utf-8 --output=nxvcontrol.pot nxvforward.py
        pygettext3 --output="${FN_TEMPLATE}" ${PARAM_FILE}
    else
        pygettext3 --output=tmp.pot ${PARAM_FILE}
        cat tmp.pot | egrep "msgid |msgstr |^$" | grep -v 'msgid ""\nmsgstr ""' >> "${FN_TEMPLATE}"
    fi

    mkdir -p translations/
    if [ ! -f "translations/en_US.po" ]; then
        msginit --input="${FN_TEMPLATE}" --locale=en_US --output-file=translations/en_US.po
    fi
    if [ ! -f "translations/zh_CN.po" ]; then
        msginit --input="${FN_TEMPLATE}" --locale=zh_CN --output-file=translations/zh_CN.po
    fi

    msgmerge --update translations/en_US.po "${FN_TEMPLATE}"
    msgmerge --update translations/zh_CN.po "${FN_TEMPLATE}"

    mkdir -p languages/en_US/LC_MESSAGES/
    msgfmt --output-file=languages/en_US/LC_MESSAGES/nxvcontrol.mo translations/en_US.po
    mkdir -p languages/zh_CN/LC_MESSAGES/
    msgfmt --output-file=languages/zh_CN/LC_MESSAGES/nxvcontrol.mo translations/zh_CN.po
}

rm -f "${FN_TEMPLATE}"

parse_pyfile "nxvforward.py nxvcontrol.py"

