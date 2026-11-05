[ -z "$AMLPATH" ] && AMLPATH=$NVBASE/modules/aml

# Audio Modification Library (AML) integration for ViPER4Android-RE
patch_aml() {
  local FILE=$1
  case $FILE in
    *.conf)
      sed -i "/v4a_standard_re {/,/}/d" $FILE
      sed -i "/v4a_re {/,/}/d" $FILE
      sed -i "s/^effects {/effects {\n  v4a_standard_re {\n    library v4a_re\n    uuid 90380da3-8536-4744-a6a3-5731970e640f\n  }/g" $FILE
      sed -i "s/^libraries {/libraries {\n  v4a_re {\n    path \/vendor\/lib\/soundfx\/libv4a_re.so\n  }/g" $FILE
      ;;
    *.xml)
      sed -i "/v4a_standard_re/d" $FILE
      sed -i "/v4a_re/d" $FILE
      sed -i "/<libraries>/ a\        <library name=\"v4a_re\" path=\"libv4a_re.so\"\/>" $FILE
      sed -i "/<effects>/ a\        <effect name=\"v4a_standard_re\" library=\"v4a_re\" uuid=\"90380da3-8536-4744-a6a3-5731970e640f\"\/>" $FILE
      ;;
  esac
}
