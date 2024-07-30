<template>
    <h3 id="version">Loading Radon...</h3>
    <br>
    <input id="namespace" placeholder="Namespace..."><br>
    <input id="pack_format" placeholder="Pack format..."><br>
    <textarea id="code" placeholder="Code..."></textarea><br>
    <div class="files"></div>
</template>

<script setup>
import "../styles/tryout.css";
</script>

<style scoped>
.container>.content {
    background-color: red;
    width: 100vw;
}

#namespace, #pack_format {
    width: 100%;
}
</style>