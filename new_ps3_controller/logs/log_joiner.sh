#!/usr/bin/env bash

mergedlog=merge-logs.log
[[ -e "${mergedlog}" ]] && \
mv -v $mergedlog last_${mergedlog}

for x in *.log ; do
	[[ "$x" == "joined.log" || "$x" == "${mergedlog}" || "$x" == "last_${megedlog}" ]] && continue
	echo "## LOG $x" > ${mergedlog}
	cat "$x" >> ${mergedlog}
	echo >> ${mergedlog}
done
