# TODO

- [ ] Extending classes and enums
- [ ] Spread syntax in arguments: `fn my_func(int a, ...float[] c)`
- [ ] Cast ints to floats and floats to ints when calling functions. (Maybe make it a config option?)
- [ ] CplFunction compile time value and storing the function declaration inside it. And also adding .call(
  List[CompileTimeValue]) function with it. Simplifying the definition of a class.
- [ ] Putting every variable in a stack?
- [ ] Try changing CplIntNBT with CplScore because it will make everything shorter if possible (The CplIntNBT can still
  stay as it is sometimes useful like command macros)
- [ ] Ability to use radon, python and mcfunction files with the import keyword
- [ ] Storing functions in variables? (by making a run_function function that runs the given function either via macros
  or by checking every function to see if it fits)
- [ ] Defining/running functions with directories
- [ ] String manipulations: <string>.split(<string>), <array>.join(<string>), <string>
  .replace(<string>, <string>), <string>.toArray()
- [ ] A macro function for loading schematic files into the world
- [ ] Classes (Just extends CplObject and add a `.className` attribute)
