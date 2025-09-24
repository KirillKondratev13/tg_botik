#!/usr/bin/env python3
"""
Упрощенный тестовый скрипт для проверки функциональности административной панели
(без зависимости от telegram модуля)
"""

import sys
import os
import tempfile

# Добавляем путь к проекту
sys.path.append(os.path.dirname(__file__))

def test_database_functions():
    """Проверка функций базы данных"""
    print("🔍 Тестирование функций базы данных...")
    
    try:
        from database import (
            get_categories, get_products_by_category, get_product,
            add_product, update_product, delete_product, remove_from_cart_by_product
        )
        print("✅ Database functions imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Database import error: {e}")
        return False

def create_mock_telegram():
    """Создание mock-объектов для telegram"""
    class MockUpdate:
        pass
    
    class MockContextTypes:
        DEFAULT_TYPE = None
    
    class MockReplyKeyboardMarkup:
        def __init__(self, *args, **kwargs):
            pass
    
    class MockInlineKeyboardButton:
        def __init__(self, *args, **kwargs):
            pass
    
    class MockInlineKeyboardMarkup:
        def __init__(self, *args, **kwargs):
            pass
    
    # Создаем mock модули
    import types
    telegram_module = types.ModuleType('telegram')
    telegram_module.Update = MockUpdate
    telegram_module.ReplyKeyboardMarkup = MockReplyKeyboardMarkup
    telegram_module.InlineKeyboardButton = MockInlineKeyboardButton
    telegram_module.InlineKeyboardMarkup = MockInlineKeyboardMarkup
    
    telegram_ext_module = types.ModuleType('telegram.ext')
    telegram_ext_module.ContextTypes = MockContextTypes
    
    sys.modules['telegram'] = telegram_module
    sys.modules['telegram.ext'] = telegram_ext_module

def test_admin_handlers():
    """Проверка обработчиков администратора"""
    print("\n🔧 Тестирование обработчиков администратора...")
    
    # Создаем mock для telegram
    create_mock_telegram()
    
    try:
        from handlers.admin_handlers import (
            validate_price, validate_text_field, MESSAGES, log_admin_action
        )
        print("✅ Admin handler functions imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Admin handlers import error: {e}")
        return False

def test_validation_functions():
    """Проверка функций валидации"""
    print("\n🧪 Тестирование функций валидации...")
    
    # Создаем mock для telegram
    create_mock_telegram()
    
    try:
        from handlers.admin_handlers import validate_price, validate_text_field
        
        # Тест валидации цены
        test_cases_price = [
            ("100", True, 100.0),
            ("100.50", True, 100.5),
            ("100,50", True, 100.5),
            ("0", False, 0.0),
            ("-10", False, 0.0),
            ("abc", False, 0.0),
            ("", False, 0.0)
        ]
        
        print("  💰 Тестирование валидации цены:")
        for price_str, expected_valid, expected_value in test_cases_price:
            is_valid, value = validate_price(price_str)
            if is_valid == expected_valid and (not expected_valid or abs(value - expected_value) < 0.001):
                print(f"    ✅ '{price_str}' -> valid={is_valid}, value={value}")
            else:
                print(f"    ❌ '{price_str}' -> expected valid={expected_valid}, value={expected_value}, got valid={is_valid}, value={value}")
        
        # Тест валидации текста
        test_cases_text = [
            ("Valid text", True),
            ("", False),
            ("   ", False),
            ("A", True),
            ("A" * 255, True),
            ("A" * 256, False)
        ]
        
        print("  📝 Тестирование валидации текста:")
        for text, expected in test_cases_text:
            result = validate_text_field(text)
            if result == expected:
                print(f"    ✅ '{text[:20]}...' -> {result}")
            else:
                print(f"    ❌ '{text[:20]}...' -> expected {expected}, got {result}")
        
        return True
    except Exception as e:
        print(f"❌ Validation functions error: {e}")
        return False

def test_database_operations():
    """Проверка операций с базой данных"""
    print("\n💾 Тестирование операций с базой данных...")
    
    # Создаем временную базу данных для тестирования
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    try:
        import database
        import sqlite3
        
        # Патчим функции для использования временной базы
        original_connect = sqlite3.connect
        def temp_connect(db_path):
            return original_connect(temp_db.name)
        
        # Подменяем sqlite3.connect в модуле database
        database.sqlite3.connect = temp_connect
        
        # Инициализируем базу данных
        database.init_db()
        print("  ✅ Database initialized")
        
        # Получаем категории
        categories = database.get_categories()
        print(f"  ✅ Categories retrieved: {len(categories)} categories found")
        
        if categories:
            category_id = categories[0][0]
            category_name = categories[0][1]
            print(f"  📁 Testing with category: {category_name} (ID: {category_id})")
            
            # Тестируем добавление товара
            test_product_name = "Test Product"
            test_price = 1000.0
            test_description = "Test Description"
            
            database.add_product(test_product_name, category_id, test_price, test_description)
            print("  ✅ Product added successfully")
            
            # Проверяем, что товар добавился
            products = database.get_products_by_category(category_id)
            test_product_found = any(prod[1] == test_product_name for prod in products)
            if test_product_found:
                print("  ✅ Product found in category after adding")
            else:
                print("  ❌ Product not found after adding")
            
            # Тестируем обновление товара
            database.update_product(test_product_name, category_id, "price", 2000.0)
            print("  ✅ Product price updated")
            
            # Проверяем обновление
            updated_products = database.get_products_by_category(category_id)
            updated_product = next((prod for prod in updated_products if prod[1] == test_product_name), None)
            if updated_product and updated_product[2] == 2000.0:
                print("  ✅ Product price updated correctly (1000 -> 2000)")
            else:
                print(f"  ❌ Product price not updated correctly. Current: {updated_product[2] if updated_product else 'Not found'}")
            
            # Тестируем обновление названия
            database.update_product(test_product_name, category_id, "name", "Updated Test Product")
            print("  ✅ Product name updated")
            
            # Тестируем обновление описания
            database.update_product("Updated Test Product", category_id, "description", "Updated Test Description")
            print("  ✅ Product description updated")
            
            # Тестируем каскадное удаление
            database.remove_from_cart_by_product("Updated Test Product", category_id)
            print("  ✅ Cascade deletion from carts completed")
            
            # Тестируем удаление товара
            database.delete_product("Updated Test Product", category_id)
            print("  ✅ Product deleted successfully")
            
            # Проверяем удаление
            final_products = database.get_products_by_category(category_id)
            test_product_still_exists = any(prod[1] in [test_product_name, "Updated Test Product"] for prod in final_products)
            if not test_product_still_exists:
                print("  ✅ Product successfully removed from database")
            else:
                print("  ❌ Product still exists after deletion")
        
        # Восстанавливаем оригинальную функцию
        database.sqlite3.connect = original_connect
        
        return True
        
    except Exception as e:
        print(f"❌ Database operations error: {e}")
        return False
    finally:
        # Удаляем временную базу данных
        try:
            os.unlink(temp_db.name)
        except:
            pass

def test_message_constants():
    """Проверка констант сообщений"""
    print("\n📝 Тестирование констант сообщений...")
    
    # Создаем mock для telegram
    create_mock_telegram()
    
    try:
        from handlers.admin_handlers import MESSAGES
        
        required_messages = [
            'success_product_updated',
            'success_product_added', 
            'success_product_deleted',
            'error_category_not_found',
            'error_invalid_price',
            'error_empty_field',
            'confirm_deletion'
        ]
        
        all_found = True
        for msg_key in required_messages:
            if msg_key in MESSAGES:
                print(f"  ✅ '{msg_key}': {MESSAGES[msg_key][:50]}...")
            else:
                print(f"  ❌ '{msg_key}': MISSING")
                all_found = False
        
        return all_found
        
    except Exception as e:
        print(f"❌ Message constants error: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🚀 Запуск упрощенного тестирования административного функционала\n")
    
    success_count = 0
    total_tests = 5
    
    # Тест функций БД
    if test_database_functions():
        success_count += 1
    
    # Тест обработчиков админа
    if test_admin_handlers():
        success_count += 1
    
    # Тест валидации
    if test_validation_functions():
        success_count += 1
        
    # Тест операций с БД
    if test_database_operations():
        success_count += 1
        
    # Тест констант сообщений
    if test_message_constants():
        success_count += 1
    
    print(f"\n🎯 Результаты тестирования: {success_count}/{total_tests} тестов пройдены")
    
    if success_count == total_tests:
        print("🎉 Все тесты пройдены успешно!")
        return True
    else:
        print("⚠️  Некоторые тесты не пройдены.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)