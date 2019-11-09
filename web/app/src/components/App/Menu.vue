<template>
    <b-navbar toggleable="md" type="dark" variant="info">
        <b-navbar-toggle target="nav_collapse"></b-navbar-toggle>
        <b-navbar-brand to="/"><img alt="logo" src="/assets/logo.png" class="logo" /></b-navbar-brand>
        <b-collapse is-nav id="nav_collapse">
            <b-navbar-nav>
                <b-nav-item to="/">Home</b-nav-item>
                <b-nav-item v-if="!$isLoggedIn" to="/login">Login</b-nav-item>
            </b-navbar-nav>

            <b-navbar-nav class="ml-auto">
                <b-nav-item v-if="$isLoggedIn" v-on:click="$signOut(); $router.push('/')" right>Logout</b-nav-item>
            </b-navbar-nav>

        </b-collapse>
    </b-navbar>
</template>

<script>
    import AuthMixin from 'padmiss-client/src/mixins/AuthMixin'

    export default {
        name: "Menu",

        mixins: [
            AuthMixin,
        ],

        data () {
            return {}
        }
    }
</script>

<style scoped>
    .logo {
        max-height: 36px;
    }

</style>