/**
 * Проверка метаданных файла на маленьких объектах {name,size}. Валидность Excel этот тест намеренно не доказывает.
 */
import { validateFileSelection } from "../components/UploadPage";
it("проверяет только доступные метаданные файла", () => {
  expect(validateFileSelection({ name: "fake.xlsx", size: 15 })).toBeNull();
  expect(validateFileSelection({ name: "report.csv", size: 15 })).toMatch(
    "расширение",
  );
  expect(validateFileSelection({ name: "empty.xlsx", size: 0 })).toMatch(
    "пустой",
  );
  expect(
    validateFileSelection({ name: "huge.xls", size: 51 * 1024 * 1024 }),
  ).toMatch("50 МБ");
});
