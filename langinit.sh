#!/bin/bash
# initialize transloation files of international languages

parse_pyfile() {
    local PARAM_PREFIX_OUTMO=$1
    shift
    local PARAM_LANGS=$1
    shift
    local PARAM_FILES=$1
    shift

    local FN_TEMPLATE="${PARAM_PREFIX_OUTMO}.pot"

    if [ ! -f "${FN_TEMPLATE}" ]; then
        # xgettext --language=Python --keyword=_ --from-code utf-8 --output=nxvcontrol.pot nxvforward.py
        pygettext3 --output="${FN_TEMPLATE}" ${PARAM_FILES}
    else
        pygettext3 --output=tmp.pot ${PARAM_FILES}
        cat tmp.pot | egrep "msgid |msgstr |^$" | grep -v 'msgid ""\nmsgstr ""' >> "${FN_TEMPLATE}"
        rm -f tmp.pot
    fi

    mkdir -p translations/
    for i in ${PARAM_LANGS}; do
        if [ ! -f "translations/${i}.po" ]; then
            msginit --input="${FN_TEMPLATE}" --locale=${i} --output-file=translations/${i}.po
        fi
        msgmerge --update translations/${i}.po "${FN_TEMPLATE}"

        mkdir -p languages/${i}/LC_MESSAGES/
        msgfmt --output-file="languages/${i}/LC_MESSAGES/${PARAM_PREFIX_OUTMO}.mo" "translations/${i}.po"
    done
}

rm -f "nxvcontrol.pot"
parse_pyfile "nxvcontrol" "en_US zh_CN" "nxvforward.py nxvcontrol.py"

