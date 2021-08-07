module.exports = {
  purge: [],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {},
  },
  variants: {
    extend: {
      height: ['hover'],
      width: ['hover'],
      padding: ['hover'],
      fontWeight: ['hover'],
      backgroundColor: ['odd'],
    },
  },
  plugins: [
     require('@tailwindcss/forms'),
  ],
}
